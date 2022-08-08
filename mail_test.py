__author__ = 'Tierprot'
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from wrapper import query
import subprocess
import smtplib
import os
import re

#TODO : logging
#TODO : bring everything in order!!!
#TODO : solveparsing args quotation marks!!!

def query_formatted(filename):
    request = query(filename)
    today = datetime.today()-timedelta(1)
    q_date_from = "\"{0}/{1:0>2}/{2:0>2}\"".format(today.year, today.month, today.day)
    q_date_till = q_date_from
    return request + " AND " + "(" + q_date_from + "[EDAT] : " + q_date_till + "[EDAT])"

def compile_msg(sender, recepients, filename):
    recepients = ",".join(recepients)
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recepients
    date = re.search(pattern, str(datetime.today()-timedelta(1))).group()
    msg['Subject'] = 'pubmed update, ' + date
    attachment = open(filename, 'r', encoding="UTF-8")
    attachment = attachment.read()
    msg.attach(MIMEText(attachment, "plain", "utf-8"))
    return  msg.as_string()

if __name__ == "__main__":

    QUERY_FILE = 'query.txt'
    pattern = re.compile(r"\d+-\d+-\d+", re.I | re.U)
    date = re.search(pattern, str(datetime.today())).group()
    output_file = date + ".txt"

    request = query_formatted(QUERY_FILE)
    request = request.replace('"', '\\"')

    try:
        run_query = subprocess.call('python wrapper.py --query {0} --output {1}'.format(request, output_file), shell=True)
    except:
        print("something went wrong")

    sender = 'e-mail@from.com'
    recepients = []


	

    try:
        print("starting mail stuff...")
        mail = smtplib.SMTP("smtp.from.com", 587)
        mail.ehlo()
        mail.starttls()
        email = sender
        pwrd = ""  #password
        mail.login(email, pwrd)
        msg = compile_msg(sender, recepients, output_file)
        mail.sendmail(sender, recepients, msg)
        mail.quit()
        print("mail dispatched successfully!")
        os.remove(output_file)
    except smtplib.SMTPAuthenticationError as error:
        print("failed to send e-mail, error:")
        print(error)
