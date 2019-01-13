#!/usr/bin/env python3

import argparse
import email
import getpass
import imapclient
import logging

parser = argparse.ArgumentParser()
parser.add_argument('source_host')
parser.add_argument('source_username')
parser.add_argument('dest_host')
parser.add_argument('dest_username')
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--copy-no-message-id', action='store_true')
args = parser.parse_args()

logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

class ImapSync:
    def __init__(self, source_host, source_username, dest_host, dest_username, dry_run, copy_no_message_id):
        self.dry_run = dry_run
        self.copy_no_message_id = copy_no_message_id
        logging.info("Connecting to source")
        self.source = imapclient.IMAPClient(source_host)
        self.source.login(source_username, getpass.getpass('Source password:'))
        self.source_list_response = self.source.list_folders()
        self.source_delimiter = self.source_list_response[0][1].decode('utf-8') # Assume delimiter for first record is the same for all. Delimiter is second field


        logging.info("Connecting to destination")
        self.dest = imapclient.IMAPClient(dest_host)
        self.dest.login(dest_username, getpass.getpass('Dest password:'))
        self.dest_list_response = self.dest.list_folders()
        self.dest_delimiter = self.dest_list_response[0][1].decode('utf-8') # Assume delimiter for first record is the same for all. Delimiter is second field

        self.create_folders()
        for folder in self.source_list_response:
            self.sync_folder(folder)
        logging.info("Complete")

    def create_folders(self):
        source_folders = [folder[2].split(folder[1].decode('utf-8')) for folder in self.source_list_response]
        for source_folder in source_folders:
            source_folder_text = self.source_delimiter.join(source_folder)
            if not self.dest.folder_exists(source_folder_text.encode('utf-8')):
                logging.info("Creating folder %s", source_folder_text)
                if not self.dry_run:
                    self.dest.create_folder(source_folder_text.encode('utf-8'))

    def get_header_message_ids(self, connection):
        imap_message_ids = connection.search()
        headers = [email.message_from_bytes(message[b'RFC822.HEADER']) for id, message in connection.fetch(imap_message_ids, ['RFC822.HEADER']).items()]
        return set(header['Message-ID'].strip() for header in headers if header['Message-ID'])

    def sync_folder(self, folder):
        logging.info("Syncing folder %s", folder)
        self.source.select_folder(folder[2], readonly=True)
        self.dest.select_folder(self.dest_delimiter.join(folder[2].split(folder[1].decode('utf-8'))).encode('utf-8'))
        destination_header_message_ids = self.get_header_message_ids(self.dest)
        logging.info("Destination message ids: %s", str(destination_header_message_ids))

        source_messages = self.source.search()
        logging.info("Source messages: %d", len(source_messages))
        copied_messages = 0
        for new_message_id in source_messages:
            logging.info("Syncing IMAP ID %s", new_message_id)
            response = self.source.fetch(new_message_id, ['FLAGS', 'RFC822', 'INTERNALDATE'])[new_message_id]
            email_message = email.message_from_bytes(response[b'RFC822'])
            flags = [flag for flag in response[b'FLAGS'] if flag.decode('utf-8').casefold()!='\\Recent'.casefold()]
            logging.info("Source email From=%s, Subject=%s ID=%s", email_message['From'], email_message['Subject'], email_message['Message-ID'])

            if email_message['Message-ID'] and email_message['Message-ID'].strip() and email_message['Message-ID'].strip() not in destination_header_message_ids:
                logging.info("Copying email From=%s, Subject=%s ID=%s", email_message['From'], email_message['Subject'], email_message['Message-ID'])
                copied_messages += 1
                if not self.dry_run:
                    self.dest.append(self.dest_delimiter.join(folder[2].split(folder[1].decode('utf-8'))), email_message.as_bytes(), flags, response[b'INTERNALDATE'])

        logging.info("Copied messages: %d", copied_messages)





ImapSync(args.source_host, args.source_username, args.dest_host, args.dest_username, args.dry_run, args.copy_no_message_id)
