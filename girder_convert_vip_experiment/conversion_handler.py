"""
This module contains the class used to provide a route to launch the execution of a 
container to convert an experiment.
"""
import hashlib
import os
import shutil
import json
import docker
import bson.json_util
from girder.constants import AccessType
from girder.api.rest import Resource
from girder.models.item import Item
from girder.models.folder import Folder
from girder.models.file import File
from girder.models.assetstore import Assetstore
from girder.models.upload import Upload
from girder.api import access
from girder.models.user import User
from girder.api.describe import Description, autoDescribeRoute
from girder.models.setting import Setting
from bson import ObjectId



from .conversion_plugin_settings import ConversionPluginSettings


class ConversionHandler(Resource):
    """Class used to provide a route to launch the execution of a container to convert an 
    experiment."""

    DEFAULT_USER = 'ANONYMOUS'

    def __init__(self):
        self.settings = Setting().get(ConversionPluginSettings.SETTING_KEY)
        super().__init__()
        self.resourceName = 'convert'
        self.settings = Setting()
        self.resourceName = 'convert'
        User().exposeFields(level=AccessType.READ, fields={'canConvert'})
        self.route('GET', (), self.launch_execution)


    @access.public
    @autoDescribeRoute(
       Description("Launch the execution of a container")
            .param('application', 'The name of the application', required=True, strip=True)
            .param('version', 'The version of the application', required=True, strip=True)
            .param('experiment_id', 'The ID of the experiment', required=True, strip=True)
            .param('container_id', 'The ID of the container', required=True, strip=True)
            .errorResponse('ID was invalid')
    )
    def launch_execution(self, application: str, version: str, experiment_id: str,
                         container_id: str):
        """Launch the execution of a container"""
        User().exposeFields(level=AccessType.READ, fields={'canConvert'})
        user = self.getCurrentUser()
        if "canConvert" not in user or user["canConvert"] is False:
            return {
                "message": "The user does not have the rights to convert an experiment",
                "type": "error"
            }
        response = {}
        folders = get_folders_from_experiment(experiment_id)
        if folders is None:
            response["message"] = "No data found for this experiment ID"
            response["type"] = "error"
        else:
            data_path = Setting().get(ConversionPluginSettings.SETTING_KEY).get("data_path")
            hashed = hashlib.md5(experiment_id.encode()).hexdigest()
            # for now, each folder corresponds to a wf
            prepare_files(folders, hashed, experiment_id)
            # save the folders in a json file
            os.makedirs(f"{data_path}/{hashed}", exist_ok=True)
            parsed = bson.json_util.dumps(folders)
            with open(f"{data_path}/{hashed}/folders.json", "w", encoding="utf-8") as json_file:
                json.dump(parsed, json_file)
            # call the container
            json_output = call_container(container_id, hashed, experiment_id)
            if json_output is None:
                response["message"] = "Error during the conversion with the container"
                response["type"] = "error"
            elif insert_result(f"{data_path}/{hashed}", json_output, application, version,
                               self.getCurrentUser()) is None:
                response["message"] = "Error during the insertion of the result in the database"
                response["type"] = "error"
            else:
                response["message"] = "The conversion was successful"
                response["type"] = "success"

        return response


def get_folders_from_experiment(exp_id):
    """Get the folders from an experiment ID"""
    results = {}
    target_name = Setting().get(ConversionPluginSettings.SETTING_KEY).get("target_name")
    request = {f"meta.{target_name}": exp_id}
    params = {
        "limit": 1000,
        "offset": 0,
        "sort": [("name", 1)]
    }
    # list of the ressources that we are looking for
    ressources = {
        "folder": Folder,
        "item": Item,
    }
    for rsc, resource_class in ressources.items():
        results[rsc] = []
        cursor = resource_class().find(request, **params)
        for r in cursor:
            results[rsc].append(r)

    # if there is no folder, return None
    return results if len(results["folder"]) != 0 \
        or len(results["item"]) != 0 else None


def call_container(container_name, hashed, exp_id):
    """Call the container to convert the data"""
    data_path = Setting().get(ConversionPluginSettings.SETTING_KEY).get("data_path")
    client = docker.from_env()
    cc = client.containers.run(
        image=container_name,
        command=hashed + "/",
        # Mount the folder in the container
        volumes={
            data_path: {
                'bind': '/vol',
                'mode': 'rw'
            },
        },
        detach=False,
        auto_remove=True
    )
    print(cc)

    output_path = f"{data_path}/{hashed}/{exp_id}_processed.json"

    return json.load(open(output_path, "r", encoding="utf-8"))


def insert_result(path, hierarchy, application, version, creator):
    """Insert the result of the conversion in the database"""
    output_id = Setting().get(ConversionPluginSettings.SETTING_KEY).get("girder_id_outputs")
    # asset
    assetstore = Assetstore().getCurrent()
    # find the folder named application or create it
    app_folder = Folder().findOne({
        "parentId": ObjectId(output_id),
        "name": application
    })
    parent_folder = Folder().findOne({
        "_id": ObjectId(output_id)
    })
    if app_folder is None:
        app_folder = Folder().createFolder(
            parent=parent_folder,
            name=application,
            public=True,
            creator=creator
        )
    # find the folder named version or create it
    vers_folder = Folder().findOne({
        "parentId": ObjectId(app_folder["_id"]),
        "name": version
    })
    if vers_folder is None:
        parent_folder = Folder().findOne({
            "_id": ObjectId(app_folder["_id"])
        })
        vers_folder = Folder().createFolder(
            parent=parent_folder,
            name=version,
            public=True,
            creator=creator
        )
    # create the hierarchy of folders
    return insert_data(hierarchy, vers_folder, creator, path, assetstore)

def insert_data(hierarchy, parent_folder, creator, path, assetstore):
    """Insert the data in the database"""
    for key, value in hierarchy.items():
        if isinstance(value, dict):
            # Check if the folder already exists
            i = 0
            folder_name = key
            while Folder().findOne({
                "parentId": ObjectId(parent_folder["_id"]),
                "name": folder_name
            }) is not None:
                i += 1
                folder_name = key + "_(" + str(i) + ")"
            # Create a folder
            folder = Folder().createFolder(
                parent=parent_folder,
                name=folder_name,
                parentType="folder",
                public=True,
                creator=creator
            )
            # Recursively insert data in the subfolder
            insert_data(value, folder, creator, path, assetstore)
        else:
            # Upload the file
            item = Item().createItem(
                name=key,
                creator=creator,
                folder=parent_folder,
                reuseExisting=True,
                description=""
            )
            # Insert the file
            file_path = os.path.join(path, value)
            size = os.path.getsize(file_path)
            name = "data.feather"

            with open(file_path, 'rb') as f:
                Upload().uploadFromFile(f, size, name, 'item', item, creator)
    return True

def prepare_files(folders, hashed, experiment_id):
    """Copy the files in the storage folder"""
    # for each folder, get the items
    data_path = Setting().get(ConversionPluginSettings.SETTING_KEY).get("data_path")
    for folder in folders["folder"]:
        items = Item().find({
            "folderId": folder["_id"]
        })

        # for each item, get the file
        for item in items:
            os.makedirs(f"{data_path}/{hashed}/{experiment_id}/{folder['name']}/{item['name']}",
                        exist_ok=True)
            file = File().findOne({
                "itemId": item["_id"]
            })
            # get the file path
            assetstore_path = Assetstore().load(file["assetstoreId"])["root"]
            path = os.path.join(assetstore_path, file["path"])
            # get the file name
            name = file["name"]
            # create the folder
            os.makedirs(
                f"{data_path}/{hashed}/{experiment_id}/{folder['name']}/{item['name']}",
                exist_ok=True
            )
            # copy the file in the folder
            shutil.copyfile(
                path,
                f"{data_path}/{hashed}/{experiment_id}/{folder['name']}/{item['name']}/{name}"
            )
