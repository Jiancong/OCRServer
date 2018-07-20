
from flask import Flask, render_template, request, send_from_directory, Response ,jsonify, make_response
from flask_restful import Resource, reqparse, Api
from restapi import tools, recognize

from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage
import hashlib

from datetime import datetime
from shutil import copyfile

import cv2
import numpy as np
import logging
import os

UPLOAD_FOLDER = './images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg',  'bmp' ])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
PREPROC_FOLDER = './preproc'
HTTP_400_BAD_REQUEST = 400
HTTP_201_CREATED = 201

class Uploader(Resource):

    def md5(self, fname):
        hash_md5 = hashlib.md5()    
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
                return hash_md5.hexdigest()

    def allowed_file(self, filename):
        file_ext=filename.rsplit('.', 1)[-1]
        status = '.' in filename and file_ext in ALLOWED_EXTENSIONS
        return file_ext, status

    def upload(self):
        return render_template('upload.html')

    def preprocess_images(self, filename, storagepath):
        '''
        filename: the file to process
        storagepath: the directory to store the result
        '''
        pass

    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('user_file', type=FileStorage, location='files')
        parse.add_argument('user_id', type=int, location='args')
        args = parse.parse_args()

        file = args['user_file']

        if file:
            if file.filename == '':
                response_data = {
                    "status": 'Upload filename is null.',
                    "status_code": HTTP_400_BAD_REQUEST 
                }
                return make_response(jsonify(response_data), HTTP_400_BAD_REQUEST) # <- the status_code displayed code on console

            print ("recieved a new file.")
            
            fext, s = self.allowed_file(file.filename)
            if s:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))

                tmppath =self.md5(os.path.join(UPLOAD_FOLDER, filename)) + "." + fext

                # preproces image file directory
                preproc_filepath = self.md5(os.path.join(UPLOAD_FOLDER, filename))
                preproc_filepath = os.path.join(PREPROC_FOLDER, preproc_filepath)

                os.rename(os.path.join(UPLOAD_FOLDER, filename), os.path.join(UPLOAD_FOLDER, tmppath))

                newfilename = os.path.join(UPLOAD_FOLDER, tmppath)

                print("tmppath=>", tmppath)
                print("newfilename=>", newfilename)
                print("preproc_filepath=>", preproc_filepath)

                if os.path.exists(newfilename):
                    response_data = {
                        "status": 'Please do not upload the file repeatedly.',
                        "status_code": HTTP_400_BAD_REQUEST
                    }
                    return make_response(jsonify(response_data), HTTP_400_BAD_REQUEST)

                if not os.path.exists(PREPROC_FOLDER):
                    os.makedirs(PREPROC_FOLDER)
                    
                copyfile(newfilename, PREPROC_FOLDER)
                    
                #self.preprocess_images(newfilename, preproc_filepath)

                response_data = {
                    "status": 'Upload file successfully',
                    "status_code": HTTP_201_CREATED
                }
                return make_response(jsonify(response_data), HTTP_201_CREATED)
            else:
                response_data = { 
                    "status": 'Upload is not allowed filetype.',
                    "status_code": HTTP_400_BAD_REQUEST
                }
                return make_response(jsonify(response_data), HTTP_400_BAD_REQUEST)

        else:
            response_data = {
                    "status": 'user_file is invalid.',
                    "status_code": HTTP_400_BAD_REQUEST
                    }
            return make_response(jsonify(response_data), HTTP_400_BAD_REQUEST)



