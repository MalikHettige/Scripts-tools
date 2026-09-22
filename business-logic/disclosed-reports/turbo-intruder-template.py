def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                           concurrentConnections=30,
                           requestsPerConnection=30,
                           pipeline=False
                           )

   for i in range(30):
	engine.queue(target.req, i)
        engine.queue(target.req, target.baseInput, gate='race1')


    engine.start(timeout=5)
   engine.openGate('race1')

    engine.complete(timeout=60)


def handleResponse(req, interesting):
	table.add(req)
