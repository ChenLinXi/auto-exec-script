def createTopic(lookupd, topic):
        res_topic = 'curl http://' + lookupd + '/create_topic?topic=' + topic
        res_channel = 'curl http://' + lookupd + '/create_channel?topic=' + topic + '\&channel=c'
        os.system(res_topic)
        os.system(res_channel)
        return 0
