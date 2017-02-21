#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gen_msg, generate e-mail message with attachment and save as file

@author: AnyMaster
https://github.com/AnyMaster/pop3fake
"""

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import Encoders
from os.path import isfile

SUBJECT = "You got a new E-mail with attachment!"
FROM = "FunGuy@Source.Test"
TO = "ToAnyPeople@Destination.Test"
MSG_FILE = "message.txt"


def gen_msg(attachment):
    """ Generate e-mail message with attachment and save as file

    :param attachment: file to attach into message
    """
    print "[*] Start to generate message."
    if not isfile(attachment):
        print "[-] File '{}' not found".format(attachment)
        exit(1)

    file_attach = MIMEBase('application', "octet-stream")
    file_attach.set_payload(open(attachment, "rb").read())
    Encoders.encode_base64(file_attach)
    file_attach.add_header('Content-Disposition',
                           'attachment; filename="{}"'.format(attachment))

    msg = MIMEMultipart()
    msg['Subject'] = SUBJECT
    msg['From'] = FROM
    msg['To'] = TO
    msg.attach(MIMEText("Text body in test mail message", "plain"))
    msg.attach(file_attach)

    with open(MSG_FILE, "wb") as f_obj:
        f_obj.write(str(msg))

    print "[+] Message saved to '{}'".format(MSG_FILE)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: gen_msg.py file_to_attach\n")
        print("Generate test mail message with file attached")
        print("Save result into 'message.txt'")
        sys.exit()
    gen_msg(sys.argv[1])
