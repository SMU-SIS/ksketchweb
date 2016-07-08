'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''

"""Data encryption

@created: Nguyen Thi Ngoc
"""
"""
Functions for encryption and decryption of data
"""

import base64
from Crypto.Cipher import AES
from appengine_config import _ConfigDefaults

class Crypto:

    #Encrypt plain text to cipher text using AES
    @staticmethod
    def encrypt(plainText):
        BLOCK_SIZE = 32
        PADDING = '{'
        try:
            if(plainText != ""):
                pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
                encodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
                cipherText = encodeAES(AES.new(_ConfigDefaults.ksketch_CRYPTO_KEY), plainText.encode('utf8'))
                return cipherText
            else:
                return plainText
        except:
            print plainText

    #Decrypt cipher text to plain text
    @staticmethod
    def decrypt(cipherText):
        PADDING = '{'
        try:
            if(cipherText != ""):
                if " " in cipherText == True:
                    cipherText = cipherText.replace(" ", "+")
                decodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
                plainText = decodeAES(AES.new(_ConfigDefaults.ksketch_CRYPTO_KEY), cipherText)
                return plainText.decode('utf8')
            else:
                return cipherText
        except:
            print cipherText