# ----------------------------------------------------------------------------
#  File:        wsgi.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: WSGI entry point for production deployment
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

from app import app as application

if __name__ == "__main__":
    application.run() 