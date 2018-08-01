#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, request, send_from_directory, Response
from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage
import hashlib

from flask_restful import Api
from restapi import ExtractImage2, Ocr2, CompressImage, DetectType2, DetectType3, recognize
from restapi.Uploader import Uploader
from restapi.DatabaseApi import FetchRecordsApi, InsertRecordApi
import logging
import argparse
from datetime import datetime
from shutil import copyfile

app = Flask(__name__)

# MySQL configurations
DB_HOST='localhost'
DB_USER='testuser'
DB_PASSWD='abcd1234'
DB_NAME='ocrserver'

api = Api(app)

logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] %(levelname)-5s %(name)-8s - %(message)s")

DEBUG_FILE_NUM=10

@app.route('/health')
def heath_check():
    return 'OK'


#api.add_resource(DetectType2.DetectType2Api, '/api/detect_invoice')
#api.add_resource(ExtractImage2.ExtractImage2Api, '/api/extract_image')
api.add_resource(Uploader, '/api/upload')
api.add_resource(DetectType3.DetectType3Api, '/api/detect_in',
        resource_class_kwargs={'DB_HOST': DB_HOST, 'DB_USER': DB_USER, 'DB_PASSWD': DB_PASSWD, 'DB_NAME': DB_NAME})
api.add_resource(FetchRecordsApi, '/api/fetchrecords', 
        resource_class_kwargs={'DB_HOST': DB_HOST, 'DB_USER': DB_USER, 'DB_PASSWD': DB_PASSWD, 'DB_NAME': DB_NAME})
api.add_resource(InsertRecordApi, '/api/insert/', 
        resource_class_kwargs={'DB_HOST': DB_HOST, 'DB_USER': DB_USER, 'DB_PASSWD': DB_PASSWD, 'DB_NAME': DB_NAME})
#api.add_resource(Ocr2.OCR2Api, '/api/ocr')
#api.add_resource(CompressImage.CompressImageApi, '/api/compress_image')

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dir", required=True,
        help="path to the directory contains source images")
args = vars(ap.parse_args())

recognize.loadConfig()

logging.debug('Load Recongize Config: %s' % str(recognize.getConfig()))

def getValidImgFileList():
    rootDir = args["dir"]
    lstValidImgFile = []
    bExitLoop = False
    for parent, dirnames, filenames in os.walk(rootDir):
        for filename in filenames:
            if filename.endswith(".jpg") or filename.endswith(".jpeg"):
                imgFile = os.path.join(parent,filename)
                lstValidImgFile.append(imgFile)
            else:
                if filename.endswith(".png") or filename.endswith(".bmp"):
                    imgFile = os.path.join(parent,filename)
                    lstValidImgFile.append(imgFile)
        if bExitLoop:
            break

    return lstValidImgFile;
    
def get_filePath_fileName(filename):  
    (filepath,tempfilename) = os.path.split(filename);  
    (shortname,extension) = os.path.splitext(tempfilename);  
    return shortname, extension

def main():
    lstVaildImgFiles = getValidImgFileList()

    obj = DetectType3.DetectType3Api()

    #obj.post()
    nIndex = 0
    for imgFile in lstVaildImgFiles:
        print(imgFile)

	# process images count not bigger than specific value
        if nIndex == DEBUG_FILE_NUM:
            break

        (strJobID, fext) = get_filePath_fileName(imgFile)

        strJobID_with_index = str(nIndex) + "_" + strJobID 
	
        print("strJobID =>", strJobID)
        strFilePath = imgFile
        obj.post2(strJobID_with_index, strFilePath)
        nIndex = nIndex + 1

def test():
    obj = DetectType3.DetectType3Api()
    strJobID="7251cc1147be4726f175a09612b05b90"

    print(strJobID)
    strFilePath = args['dir'] + "/" + strJobID +".jpg"
    obj.post2(strJobID, strFilePath)
    pass


if __name__ == '__main__':
    #app.run(host='0.0.0.0', debug=True)
    app.run(debug=True)
    #main()
    #test()
