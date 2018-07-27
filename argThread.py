import threading
class Destination:
    def run(self,name,config):
        print('In thread')
        print(name)
        print(config)
        
destination = Destination()
destination_name = 'seojeong'
destination_config = 'iitp'
thread = threading.Thread(target=destination.run, args=(destination_name, destination_config))
thread.start()