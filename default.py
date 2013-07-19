import sys
import e32
import urllib
import string
from socket import *
import telephone
import time
# for contacts
import contacts
import re

# ====================================
# Contacts Search Engine
#=====================================

contacts_cache = []
new_call = 0
settings = {}

####################################################
def log(mesg, exp = None):
	"Writes the debug.log file"
	mesg = repr(time.time()) + ": " + mesg + u'\n'
	print mesg
	f = open(u'e:\\sdialer.log', 'a+')
	f.write(mesg)
	f.close()

def get_contacts_info(contacts_list, name_order):
    log(">> get_contacts_info")
    info_list = []
    # open database
    db = contacts.open()
    
    field1 = u''
    field2 = u''
    
    if name_order == "0":
        field1 = u'first_name'
        field2 = u'last_name'
    elif name_order == "1":
        field2 = u'first_name'
        field1 = u'last_name'
    
    # add info into list
    for i in contacts_list:
        info = []
        # hlight_index
        info.append(i[2])
        
        # make fullname
        title = u''
        if db[i[0]].find(field1):
            title = unicode(db[i[0]].find(field1)[0].value)
        if db[i[0]].find(field2):
            title += u' ' + unicode(db[i[0]].find(field2)[0].value)

        # fullname
        info.append(title.strip(u' '))
        
        # mobile number
        if db[i[0]].find(u'mobile_number'):
            for num in db[i[0]].find(u'mobile_number'):
                if len(num.value) > 0: info.append(unicode(num.value))

        # phone number
        if db[i[0]].find(u'phone_number'):
            for num in db[i[0]].find(u'phone_number'):
                if len(num.value) > 0: info.append(unicode(num.value))
        
        # info(hlight_index, fullname, mobile, phone)
        info_list.append(info)

    # return list
    print "info_list: " + repr(info_list)
    return info_list

####################################################
def build_cache(name_order):
    log(">> build_cache")
    # open database
    db = contacts.open()
    log("db.open")
    
    all_keys = db.keys()
    
    field1 = u''
    field2 = u''
    
    if name_order == "0":
        field1 = u'first_name'
        field2 = u'last_name'
    elif name_order == "1":
        field2 = u'first_name'
        field1 = u'last_name'
    
    log("name_order set")
    
    try:
        for i in all_keys:
            title = u''
            if db[i].find(field1):
                title = urllib.quote(unicode(db[i].find(field1)[0].value).lower())
            if db[i].find(field2):
                title += u' ' + urllib.quote(unicode(db[i].find(field2)[0].value).lower())
            
            tile = title.strip(u' ')
            #log("- list.append: " + title)
            if len(title) > 0:
                contacts_cache.append((i, title))
    except:
        log("- build_cache execpt: " + repr(sys.exc_info()))

    log("- build_cache done: " + str(len(contacts_cache)))

####################################################
def complie_regex(user_input, search_filter):
    regex_map = [u'[ ]', u'[-()]', u'[a-cA-C]', u'[d-fD-F]', u'[g-iG-I]', u'[j-lJ-L]', u'[m-oM-O]', u'[p-sP-S]', u'[t-vT-V]', u'[w-zW-Z]']
    re_pattern = u'' + search_filter # \\b | ^ | (none) from setings
    
    # get array of search key maps
    for j in user_input:
        re_pattern += regex_map[int(j)]

    return re_pattern

####################################################
def search_cache(re_pattern_srt):
    contacts_list = []
    re_pattern = re.compile(re_pattern_srt)
    #print repr(re_pattern)

    for contact in contacts_cache:
        # look in "title" column
        entry = contact[1]
        
        result = re_pattern.search(entry)

        if result is not None:
            #print repr(result.group(0))
            # add in contacts_list(id, name, hlight_index)
            contacts_list.append((contact[0], contact[1], result.start()))
            # ID, hlight_index, name (for sorting)
        
    return contacts_list

####################################################
def search(search_term, search_filter, search_type):
    # init lists
    contacts_list = []
    search_result = []
    
    # query search term
    search_str = unicode(search_term)
    filter_str = u'^'
    
    if search_filter == "0":
        filter_str = u'^'
    elif search_filter == "1":
        filter_str = u'\\b'
    elif search_filter == "2":
        filter_str = u''
    
    # make search regex (search_string, search_filter)
    re_pattern_srt = complie_regex(search_str, filter_str) #u'^') # \\b
    
    #print u're_pattern_srt: ' + re_pattern_srt
    
    # perform search on cache
    contacts_list = search_cache(re_pattern_srt)
    # sort search results
    contacts_list.sort(lambda x, y: cmp(x[1], y[1]))
    # keep top 5
    if len(contacts_list) > 5:
        contacts_list = contacts_list[0:5]
    
    # get contacts info from db (list, name_order[0=fl, 1=lf])
    search_result = get_contacts_info(contacts_list, search_type)
    
    # info(hlight_index, fullname, mobile, phone)
    return search_result

####################################################
def save_settings(dict):
    f = file("c:\\settings.ini", "w")
    for key, value in dict.items():
        print >> f, "%s: %s" % (key, value)
    f.close()


####################################################
def load_settings():
    #settings = {'name_order': 0, 'search_filter': '\\b', 'hlight_result': 0, 'result_count': 3}
    f = file("c:\\settings.ini", "r")
    dict = {}
    for line in f:
        key, value = line.split(":")
        dict[key.strip()] = value.strip()
    f.close()
    return dict

# ====================================
# HTTP Server Classes
# ====================================
class Request:
    def __init__(self, rawCommand, attributes):
        self.__attributes=attributes
        self.__rawCommand = rawCommand
    def getRawCommand(self):
        return self.__rawCommand
    def setAttributes(self, attributes):
        self.__attributes = attributes
    def getAttributes(self):
        return self.__attributes
    def getProperty(self, key):
        return self.__attributes[key]
    def setProperty(self, key, value):
        self.__attributes[key]=value

class Response:
    def __init__(self):
        self.__response=""
    def println(self, message):
        self.__response=self.__response+message #+"\r\n"
    def getResponse(self):
        rsp = "HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: %d\r\nConnection: Close\r\n\r\n" % len(self.__response)
        rsp += self.__response
        return rsp
    
class HTTPServer:
    def __init__(self, host, port):
        self.host = host;
        self.port = port;
        self.callbacks={}
    
    def doGet(self, request, response):
        pass
    def doPost(self, request, response):
        pass
    
    def __handlerAttributes(self, rawAttributes):
        rawAttributes=rawAttributes[:len(rawAttributes)-2]
        map={}
        for i in rawAttributes:
            map[i[:i.find(':')]]=i[i.find(':')+2:len(i)-1]
        return map
        
    def __handlerRequest(self, connection, rawRequest):
        self._rawRequest = rawRequest
        tokenizedLine=self._rawRequest.split('\n')
        requestLine=tokenizedLine[0]
        attributes = self.__handlerAttributes(tokenizedLine[1:])
        tokenizedLine = requestLine.split()
        attributes["request-method"]=tokenizedLine[0]
        print "request-method: " + attributes["request-method"]
        attributes["requisition"]=tokenizedLine[1]
        print "requisition: " + attributes["requisition"]
        attributes["http-version"]=tokenizedLine[2]
        print "http-version: " + attributes["http-version"]
        request_object = attributes["requisition"]
        print "request-object: " + request_object
        if request_object.startswith('/'):
            request_object=request_object[1:]
        objects=request_object.split('?')
        attributes["object-requested"]=objects[0]
        map={}
        if len(objects)>1:
                objects=objects[1].split('&')
                for i in objects:
                    iObject = i.split('=')
                    map[iObject[0]]=urllib.unquote(iObject[1])
        attributes["parameters"]=map
        request = Request(self._rawRequest, attributes)
        response = Response()
        if attributes["request-method"]=='GET':
            self.doGet(request, response)
        elif attributes["request-method"]=='POST':
            self.doPost(resquest, response)
        rsp = response.getResponse()
        print("raw rsp: " + rsp)
        connection.send(rsp)
        connection.close()
        print "= req ended. connection closed."

    def startServer(self):
        self.tcp = socket(AF_INET, SOCK_STREAM)
        orig = (self.host, self.port)
        print orig
        self.tcp.bind(orig)
        self.tcp.listen(1)
        print "** Server On"

        while True:
            try:
                con, cliente = self.tcp.accept()
                request = con.recv(1024)
            except Exception:
                print "** Error: Cannot accept client."
                break
            try:
            	print("===========================")
                self.__handlerRequest(con, request)
            except Exception:
                try:
                    con.send('Bad Request Message')
                except Exception:
                    print "** Error: Internal server error!"
                    break
            con.close()
        
        print "** server stopped!"
    
    def stopServer(self):
        print "stopServer"
        self.tcp.close()

    def addCallBack(self, key, callback):
        self.callbacks[key]=callback

class MyServer(HTTPServer):
    def __init__(self,host, port):
        HTTPServer.__init__(self, host, port)
    
    def doGet(self, request, response):
        functionName=request.getProperty("object-requested")
        attributes=request.getProperty("parameters")
        response.println(str(self.callbacks[functionName](attributes)))

# ======================
# Setup server commands
# ======================
def get_policy():
	print ">> get_policy"
	return u'<?xml version="1.0"?><cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>'

def close_server(self):
	server.stopServer()
	return u'cmd=close_server&status=0'

def do_init(attributes):
    print ">> do_init"
	
    result = u'cmd=init&status='

    if len(contacts_cache) > 0:
        result += u'0'
    else:
        result += u'1'

    # send response to client
    print "result: " + result
    return result

def do_reindex(attributes):
    print ">> do_reindex"
	
    # make cache
    build_cache(attributes["type"])

    # send response to client
    return u'cmd=reindex&status=0'

def do_search(attributes):
    print ">> do_search: " + attributes["keys"]
    
    search_result = search(unicode(attributes["keys"]), attributes["filter"], attributes["type"])
    #print "== search results:\n" + repr(result)
    
    # prepare response
    result_str = u'cmd=search&status=0&count=' + str(len(search_result))
    #print result_str

    # info(hlight_index, fullname, mobile, phone)
    for i in range(len(search_result)):
        result_str += u'&c%d=' % i
        sub_str = u''
        print u'loop: %s' % unicode(search_result[i][1])
        for j in range(len(search_result[i])):
            sub_str += urllib.quote(unicode(search_result[i][j]))
            if j < len(search_result[i]) - 1: sub_str += u'|'
        
        result_str += sub_str

    print result_str

    # send response to client
    # return u'status=0&data=' + urllib.quote(repr(result_str))
    #print "result_str: " + urllib.quote(repr(result_str))
    #return u'status=0&data=' + urllib.quote(result_str)
    return result_str

def do_dial(attributes):
    print ">> do_dial: " + unicode(attributes["number"])
    result = u'cmd=dial&status='
    global new_call
    
    try:
        # clear previous call request from pys60
        if new_call == 1:
            telephone.hang_up()
            new_call = 0;

        number = unicode(attributes["number"])
        number = number.replace(" ", "").replace("-", "")
        
        # hide dialer app
        e32.start_exe(u'ailaunch.exe', u'')
        
        # dial number
        telephone.dial(number)
        new_call = 1
        result += u'0'
    except:
        print "** unable to dial number: " + repr(sys.exc_info())
        result += u'1'

    return result

def do_hide(attributes):
    print ">> do_hide"
    result = u'cmd=hide&status='
    
    try:
        # hide dialer app
        e32.start_exe(u'ailaunch.exe', u'')
        result += u'0'
    except:
        print "** hide error: " + repr(sys.exc_info())
        result += u'1'

    return result

# init server
server = MyServer("127.0.0.1", 2192)
#server = MyServer("192.168.0.189", 2192)

# setup commands
server.addCallBack("crossdomain.xml", get_policy)
server.addCallBack("close_server", close_server)
server.addCallBack("hide", do_hide)
server.addCallBack("init", do_init)
server.addCallBack("reindex", do_reindex)
server.addCallBack("search", do_search)
server.addCallBack("dial", do_dial)

# start listening
server.startServer()

