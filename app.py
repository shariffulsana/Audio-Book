from flask import Flask, request, render_template,url_for
from flask_cors import cross_origin
import boto3
import os
from werkzeug.utils import secure_filename
import time


app = Flask(__name__)

@app.route("/")
@cross_origin()
def home():
    return render_template("index.html")


@app.route("/convert", methods = ["GET", "POST"])
@cross_origin()
def convert():
    if request.method=='POST':

        def startJob(s3BucketName, objectName):
            response = None
            client = boto3.client('textract',region_name='us-east-1')
            response = client.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': s3BucketName,
                    'Name': objectName
                }
            })

            return response["JobId"]

        def isJobComplete(jobId):
            # For production use cases, use SNS based notification 
            # Details at: https://docs.aws.amazon.com/textract/latest/dg/api-async.html
            time.sleep(5)
            client = boto3.client('textract',region_name='us-east-1')
            response = client.get_document_text_detection(JobId=jobId)
            status = response["JobStatus"]
            print("Job status: {}".format(status))

            while(status == "IN_PROGRESS"):
                time.sleep(5)
                response = client.get_document_text_detection(JobId=jobId)
                status = response["JobStatus"]
                print("Job status: {}".format(status))

            return status

        def getJobResults(jobId):

            pages = []

            client = boto3.client('textract',region_name='us-east-1')
            response = client.get_document_text_detection(JobId=jobId)
            
            pages.append(response)
            print("Resultset page recieved: {}".format(len(pages)))
            nextToken = None
            if('NextToken' in response):
                nextToken = response['NextToken']

            while(nextToken):

                response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)

                pages.append(response)
                print("Resultset page recieved: {}".format(len(pages)))
                nextToken = None
                if('NextToken' in response):
                    nextToken = response['NextToken']

            return pages

        # Document
        s3BucketName = "pdftranslate"
        documentName = "document.pdf"

        jobId = startJob(s3BucketName, documentName)
        print("Started job with id: {}".format(jobId))
        if(isJobComplete(jobId)):
            response = getJobResults(jobId)

        #print(response)

        # Print detected text
        for resultPage in response:
            for item in resultPage["Blocks"]:
                if item["BlockType"] == "LINE":
                    translated = open("static/translated.txt","w+")
                    translated.write(str(item["Text"]+''))
            translated.close()

        return render_template("index.html",conversion="Your document has been converted to text.  To Translate refer Sentence Translator")
    else:
        return render_template("index.html")




@app.route("/audio", methods = ["GET", "POST"])
@cross_origin()
def audio():
    if request.method=='POST':

        def startJob(s3BucketName, objectName):
            response = None
            client = boto3.client('textract',region_name='us-east-1')
            response = client.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': s3BucketName,
                    'Name': objectName
                }
            })

            return response["JobId"]

        def isJobComplete(jobId):
            # For production use cases, use SNS based notification 
            # Details at: https://docs.aws.amazon.com/textract/latest/dg/api-async.html
            time.sleep(5)
            client = boto3.client('textract',region_name='us-east-1')
            response = client.get_document_text_detection(JobId=jobId)
            status = response["JobStatus"]
            print("Job status: {}".format(status))

            while(status == "IN_PROGRESS"):
                time.sleep(5)
                response = client.get_document_text_detection(JobId=jobId)
                status = response["JobStatus"]
                print("Job status: {}".format(status))

            return status

        def getJobResults(jobId):

            pages = []

            client = boto3.client('textract',region_name='us-east-1')
            response = client.get_document_text_detection(JobId=jobId)
            
            pages.append(response)
            print("Resultset page recieved: {}".format(len(pages)))
            nextToken = None
            if('NextToken' in response):
                nextToken = response['NextToken']

            while(nextToken):

                response = client.get_document_text_detection(JobId=jobId, NextToken=nextToken)

                pages.append(response)
                print("Resultset page recieved: {}".format(len(pages)))
                nextToken = None
                if('NextToken' in response):
                    nextToken = response['NextToken']

            return pages

        # Document
        s3BucketName = "pdftranslate"
        documentName = "document.pdf"

        jobId = startJob(s3BucketName, documentName)
        print("Started job with id: {}".format(jobId))
        if(isJobComplete(jobId)):
            response = getJobResults(jobId)

        #print(response)

        # Print detected text
        for resultPage in response:
            for item in resultPage["Blocks"]:
                if item["BlockType"] == "LINE":
                    translated = open("static/translated.txt","w+")
                    translated.write(str(item["Text"]+''))
            translated.close()
        
        polly = boto3.client(service_name='polly',region_name='us-east-1')

        print('Starting the Polly Service')

        translated = open("static/translated.txt","r")
        text = translated.read()

        response = polly.synthesize_speech(OutputFormat='mp3', VoiceId='Brian',
                     Text=text)

        file = open('speech.mp3', 'wb')
        file.write(response['AudioStream'].read())
        file.close()
        print("Polly's output stored !")

        return render_template("index.html",conversion="Your document has been converted to text.  To Translate refer Sentence Translator")
    else:
        return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)
