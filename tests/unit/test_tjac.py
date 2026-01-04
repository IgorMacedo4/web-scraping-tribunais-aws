import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../hello_world')))
from crawlers.tjac import tjac

processo = '0716614-95.2024.8.01.0001' #ou outro processo TJAC : 0716614-95.2024.8.01.0001
print(tjac(processo))