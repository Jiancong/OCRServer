from flask_restful import Resource, reqparse, Api
import cv2
import numpy as np
from restapi import tools
import logging
from restapi import recognize

import os
from flask import Flask, render_template, request, send_from_directory, Response
from werkzeug import secure_filename
import hashlib
from datetime import datetime
from shutil import copyfile

UPLOAD_FOLDER = './images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg',  'bmp' ])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
PREPROC_FOLDER = './preproc'

class Uploader(Resource):

    def md5(fname):
        hash_md5 = hashlib.md5()    
        with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
            return hash_md5.hexdigest()

    def allowed_file(filename):
        file_ext=filename.rsplit('.', 1)[-1]
        status = '.' in filename and file_ext in ALLOWED_EXTENSIONS
        return file_ext, status

    def upload():
        return render_template('upload.html')

    def preprocess_images(filename, storagepath):
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
                return 'Upload invalid filename', status.HTTP_400_BAD_REQUEST

            
            fext, s = allowed_file(file.filename)
            if s:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))

                tmppath = md5(os.path.join(UPLOAD_FOLDER, filename)) + "." + fext

                # preproces image file directory
                preproc_filepath = md5(os.path.join(UPLOAD_FOLDER, filename))
                preproc_filepath = os.path.join(PREPROC_FOLDER, preproc_filepath)

                os.rename(os.path.join(UPLOAD_FOLDER, filename), os.path.join(UPLOAD_FOLDER, tmppath))
                newfilename = os.path.join(UPLOAD_FOLDER, tmppath)

                print("tmppath=>", tmppath)
                print("newfilename=>", newfilename)
                print("preproc_filepath=>", preproc_filepath)

                if not os.path.exists(PREPROC_FOLDER):
                    os.makedirs(PREPROC_FOLDER)
                    
                    if not os.path.exists(preproc_filepath):
                        os.makedirs(preproc_filepath)
                    
                    preprocess_images(newfilename, preproc_filepath)
                return 'Uploaded file successfully', status.HTTP_201_CREATED)
        return 'Upload invalid filename', status.HTTP_400_BAD_REQUEST


