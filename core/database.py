"""
SQLite Database Manager for download history and queue management.
"""
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
