import urllib2, urllib, zlib, hmac, hashlib, time, json
from pprint import pprint
import requests, time
from log import Log
from log import GetException


class replaceContent():
    def __init__(self):
        self.root_url = 'http://services.uplynk.com'
        self.owner = ''
        self.secret = ''
        self.slicer_url = 'http://localhost:65009'
        self.channel_guid = ''
        self.max_slate_duration = 3600 * 10 # 10 hours

    def Call(self, uri, **msg):
        msg['_owner'] = self.owner
        msg['_timestamp'] = int(time.time())
        msg = json.dumps(msg)
        msg = zlib.compress(msg, 9).encode('base64').strip()
        sig = hmac.new(self.secret, msg, hashlib.sha256).hexdigest()
        body = urllib.urlencode(dict(msg=msg, sig=sig))
        return json.loads(urllib2.urlopen(self.root_url + uri, body).read())


    def replace(self):
        live_asset = None
        # Check for live assets that are in slicing state
        asset_list = self.Call('/api2/asset/list')['assets']
        asset_duration = 0
        for asset in asset_list:
            if asset['state'] == 'slicing' and asset['job_type'] =='live' :
                # Use channel api to confirm the asset
                channel_assets = self.Call('/api2/channel/assets', id=self.channel_guid)['assets']
                for channel_asset in channel_assets:
                    if channel_asset == asset['id']:
                        live_asset = asset['id']
                        asset_duration = asset['duration']
                        break

        if not live_asset:
            Log.logEvent('CONTENT_REPLACE', meta={'type':'Could not confirm currently slicing asset'})
        else:
            Log.logEvent('CONTENT_REPLACE', meta={'type':'Asset currently slicing: ' + live_asset})

            # Set its external id
            update_meta = self.Call('/api2/asset/update', id=live_asset, external_id=live_asset)

            # Figure out how many times the asset has to be looped
            loop_count = int(self.max_slate_duration//asset_duration)

            time.sleep(1)

            loop_list = []

            for i in range(12):
                loop_list.append({"external_id": live_asset, "duration": asset_duration})

            # Call replace content
            uri = '/replace_content'
            body = {"duration": self.max_slate_duration, "replacements": loop_list}
            Log.logEvent('CONTENT_REPLACE', meta={'type':'Liveslicer request body: ' + json.dumps(body)})
            replace = requests.request("POST", self.slicer_url + uri, data=json.dumps(body))
            Log.logEvent('CONTENT_REPLACE', meta={'type':'Liveslicer response: ' + replace.text})
