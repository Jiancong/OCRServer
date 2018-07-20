#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, request, send_from_directory, Response
from werkzeug import secure_filename
import hashlib

from flask_restful import Api
from restapi import ExtractImage2, Ocr2, CompressImage, DetectType2, DetectType3, recognize
import logging
import argparse
from datetime import datetime
from shutil import copyfile

logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] %(levelname)-5s %(name)-8s - %(message)s")

app = Flask(__name__)

DEBUG_FILE_NUM=10

@app.route('/health')
def heath_check():
    return 'OK'

api = Api(app)

api.add_resource(DetectType2.DetectType2Api, '/api/detect_invoice')
api.add_resource(ExtractImage2.ExtractImage2Api, '/api/extract_image')
api.add_resource(Uploader, '/api/upload')
api.add_resource(Ocr2.OCR2Api, '/api/ocr')
api.add_resource(CompressImage.CompressImageApi, '/api/compress_image')
api.add_resources()

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
            if filename.endswith(".jpg"):
                imgFile = os.path.join(parent,filename)
                lstValidImgFile.append(imgFile)
        if bExitLoop:
            break

    return lstValidImgFile;
    
def get_filePath_fileName(filename):  
    (filepath,tempfilename) = os.path.split(filename);  
    (shotname,extension) = os.path.splitext(tempfilename);  
    return shotname

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

        strJobID = str(nIndex) + "_" + get_filePath_fileName(imgFile)
	
        print("strJobID =>", strJobID)
        strFilePath = imgFile
        obj.post2(strJobID, strFilePath)
        nIndex = nIndex + 1

def test():
    obj = DetectType3.DetectType3Api()
    strJobID="04d6ebe32c3cd82303594fb686fceac5"
    #strJobID = "125cf02f30721a3563c733975314b234"
    print(strJobID)
    strFilePath = args['dir'] + "/" + strJobID +".jpg"
    obj.post2(strJobID, strFilePath)
    pass


if __name__ == '__main__':
    app.run(debug=True)
    #main()
    #test()
