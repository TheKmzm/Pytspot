import json
import os

class SpotifyClient:
    def __init__(self):
        self.path = os.path.join("data","locals_lists")
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)

    def save_item_locally(self, data, name="saved_items"):
        """Saves a track/artist/playlist dict to a local JSON file."""
        pth = os.path.join(self.path, name + ".json")
        items = self.get_saved_items(name=name)
        
        # Check for duplicates (by URI)
        for i in items:
            if i.get('uri') == data.get('uri'):
                print("Item already saved.")
                return False
        
        items.append(data)
        
        try:
            with open(pth, 'w') as f:
                json.dump(items, f, indent=4)
            print(f"Saved: {data['name']}")
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def get_saved_items(self, name="saved_items"):
        """Reads the local JSON file."""
        pth = os.path.join(self.path, name + ".json")
        if not os.path.exists(pth):
            return []
        try:
            with open(pth, 'r') as f:
                return json.load(f)
        except:
            return []

    def remove_item_locally(self, uri, name="saved_items"):
        """Removes an item by URI."""
        pth = os.path.join(self.path, name + ".json")
        items = self.get_saved_items(name=name)
        
        new_items = [i for i in items if i.get('uri') != uri]
        
        try:
            with open(pth, 'w') as f:
                json.dump(new_items, f, indent=4)
            print(f"Removed item with URI: {uri}")
            return True
        except Exception as e:
            print(f"Remove error: {e}")
            return False

if __name__ == "__main__":
    client = SpotifyClient()
    print(client.get_saved_items())
