# imapsync
imapsync copies / synchronises emails and folders from one IMAP account to another IMAP account. imapsync uses imapclient library to implement a copy / synchronise between IMAP accounts. I wrote it after other IMAP copy scripts couldn't handle common corner cases.

imapclient does most of the heavy lifting to ensure a robust copy / sync script.

# Prerequisites
Python 3
pip3 install imapclient

# Arguments
Usage: imapsync.py [-h] [--dry-run] [--copy-no-message-id]
                   source_host source_username dest_host dest_username

* source_host: source IMAP host to copy from
* source_username: source IMAP username to copy from (may be your whole email address or just the user part of your email address)
* dest_host: destination IMAP host to copy to
* dest_username: destination IMAP username to copy to (may be your whole email address or just the user part of your email address)
* you will be asked for source password
* you will be asked for destination password
* --dry-run: do not create new folders or messages on the destination
* --copy-no-message-id: if a message doesn't have a message id then copy it. *This may cause duplicates*
