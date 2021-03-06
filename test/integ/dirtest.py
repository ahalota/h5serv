##############################################################################
# Copyright by The HDF Group.                                                #
# All rights reserved.                                                       #
#                                                                            #
# This file is part of H5Serv (HDF5 REST Server) Service, Libraries and      #
# Utilities.  The full HDF5 REST Server copyright notice, including          #
# terms governing use, modification, and redistribution, is contained in     #
# the file COPYING, which can be found at the root of the source code        #
# distribution tree.  If you do not have access to this file, you may        #
# request a copy from help@hdfgroup.org.                                     #
##############################################################################
import requests
import config
import helper
import unittest
import json
import os

class DirTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(DirTest, self).__init__(*args, **kwargs)
        self.endpoint = 'http://' + config.get('server') + ':' + str(config.get('port'))
        self.user1 = {'username':'test_user1', 'password':'test'}
    
        
    def testGetToc(self):  
        domain = config.get('domain')  
        if domain.startswith('test.'):
            domain = domain[5:]
        req = self.endpoint + "/"
        headers = {'host': domain}
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.headers['content-type'], 'application/json')
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
        root_uuid = rspJson['root']
        req = self.endpoint + "/groups/" + root_uuid 
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        # get top-level links
        req = self.endpoint + "/groups/" + root_uuid + "/links"
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue("links" in rspJson)
        links = rspJson["links"]
         
        home_dir = config.get("home_dir")
        for item in links:
            if item['title'] == home_dir:
                self.assertTrue(False)  # should not see home dir from root toc
        req = self.endpoint + "/groups/" + root_uuid + "/links/test" 
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue("link" in rspJson)
        link = rspJson['link']
        group_uuid = link['id']
        req = self.endpoint + "/groups/" + group_uuid + "/links/tall" 
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue("link" in rspJson)
        link = rspJson['link']
        self.assertEqual(link['class'], 'H5L_TYPE_EXTERNAL')
        self.assertEqual(link['title'], 'tall')
        self.assertEqual(link['h5path'], '/')
        self.assertEqual(link['h5domain'], 'tall.test.' + domain)
        
    def testGetUserToc(self):  
        domain = config.get('domain')
        if domain.startswith('test.'):
            domain = domain[5:]  # backup over the test part
      
        home_dir = config.get("home_dir")
        user_domain = self.user1['username'] + '.' + home_dir  + '.' + domain
        req = self.endpoint + "/"
        headers = {'host': user_domain}
        # this should get the users .toc file
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.headers['content-type'], 'application/json')
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
        root_uuid = rspJson['root']
        req = self.endpoint + "/groups/" + root_uuid 
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        
        if os.name == 'nt':
            return # symbolic links used below are not supported on Windows
            
        # get link to 'public' folder
        req =  self.endpoint + "/groups/" + root_uuid + "/links/public"
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        
        rspJson = json.loads(rsp.text)
        self.assertTrue("link" in rspJson)
        link_json = rspJson["link"]
        self.assertEqual(link_json["class"], "H5L_TYPE_EXTERNAL")
        self.assertEqual(link_json["title"], "public")
        self.assertEqual(link_json["h5domain"], domain) 
        self.assertEqual(link_json["h5path"], "/public") 
        
        # get link to 'tall' file
        req =  self.endpoint + "/groups/" + root_uuid + "/links/tall"
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        
        rspJson = json.loads(rsp.text)
        self.assertTrue("link" in rspJson)
        link_json = rspJson["link"]
        self.assertEqual(link_json["class"], "H5L_TYPE_EXTERNAL")
        self.assertEqual(link_json["title"], "tall")
        self.assertEqual(link_json["h5domain"], "tall." + user_domain)

        
    def testPutUserDomain(self):  
        domain = config.get('domain')
        home_dir = config.get("home_dir")
        if domain.startswith('test.'):
            domain = domain[5:]  # backup over the test part
      
        user_domain = self.user1['username'] + '.' + home_dir + '.' + domain
        
        # this should get the users .toc file
        headers = {'host': user_domain }
        req = self.endpoint + '/'
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
        toc_root_uuid = rspJson['root']
        req = self.endpoint + "/groups/" + toc_root_uuid 
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
       
        
        # verify that "myfile" doesn't exist yet
        user_file = "myfile." + user_domain
        req = self.endpoint + "/"
        headers = {'host': user_file}
        #verify that the domain doesn't exist yet
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 404)
        
        # do a put on "myfile"
        rsp = requests.put(req, headers=headers)
        self.assertEqual(rsp.status_code, 201)
        
        # now the domain should exist  
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        
        # go back to users toc and get "/home" group
        headers = {'host': user_domain }
        req = self.endpoint + "/groups/" + toc_root_uuid + "/links/home"
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        link = rspJson['link']
        self.assertTrue('id' in link)
        toc_home_uuid = link['id']
        
        # get the user_id group
        req = self.endpoint + "/groups/" + toc_home_uuid + "/links/" + self.user1['username']
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        link = rspJson['link']
        self.assertTrue('id' in link)
        toc_user_uuid = link['id']
        
        # check that the link exists in the user toc
        headers = {'host': user_domain }
        req = self.endpoint + "/groups/" + toc_user_uuid + "/links/myfile"
        rsp = requests.get(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
      
        
    def testNoHostHeader(self):
        req = self.endpoint + "/"
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        self.assertEqual(rsp.headers['content-type'], 'application/json')
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
                   
    
    def testPutDomain(self): 
        domain_name = "dirtest_putdomain"
        
        # get toc root uuid
        req = self.endpoint + "/"
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
        toc_root_uuid = rspJson['root']
        
        # get toc 'test' group uuid
        req = self.endpoint + "/groups/" + toc_root_uuid 
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        req = self.endpoint + "/groups/" + toc_root_uuid + "/links/test" 
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue("link" in rspJson)
        link = rspJson['link']
        test_group_uuid = link['id']
        
                
        # verify that the domain name is not present
        req = self.endpoint + "/groups/" + test_group_uuid + "/links/" + domain_name 
        rsp = requests.get(req)
        self.assertTrue(rsp.status_code in (404, 410))
        
        # create a new domain
        domain = domain_name + '.' + config.get('domain')
        req = self.endpoint + "/"
        headers = {'host': domain}
        rsp = requests.put(req, headers=headers)
        self.assertEqual(rsp.status_code, 201)
        rspJson = json.loads(rsp.text)
        
        # external link should exist now
        req = self.endpoint + "/groups/" + test_group_uuid + "/links/" + domain_name 
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        
        # delete the domain
        req = self.endpoint + "/"
        headers = {'host': domain}
        rsp = requests.delete(req, headers=headers)
        self.assertEqual(rsp.status_code, 200)
        
        # external link should be gone
        req = self.endpoint + "/groups/" + test_group_uuid + "/links/" + domain_name 
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 410)      
        
    def testDeleteToc(self):
        #test DELETE toc
        req = self.endpoint + "/"
        rsp = requests.delete(req)
        self.assertEqual(rsp.status_code, 403)
        
    def testPutToc(self):
        # test PUT toc
        req = self.endpoint + "/"
        rsp = requests.put(req)
        # status code be Forbiden or Conflict based on TOC file
        # existing or not
        self.assertTrue(rsp.status_code in (403, 409))
        
    def testDeleteRoot(self):
        req = self.endpoint + "/"
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
        root_uuid = rspJson['root']
        req = self.endpoint + "/groups/" + root_uuid 
        rsp = requests.delete(req)
        self.assertEqual(rsp.status_code, 403)
        
    def testPutLink(self):
        req = self.endpoint + "/"
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
        root_uuid = rspJson['root']
        name = 'dirtest.testPutLink'
        req = helper.getEndpoint() + "/groups/" + root_uuid + "/links/" + name 
        payload = {"h5path": "somewhere"}
        # verify softlink does not exist
        rsp = requests.get(req, data=json.dumps(payload))
        self.assertEqual(rsp.status_code, 404)
        # make request
        rsp = requests.put(req, data=json.dumps(payload))
        self.assertEqual(rsp.status_code, 403)
        
    def testDeleteLink(self):
        req = self.endpoint + "/"
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        rspJson = json.loads(rsp.text)
        self.assertTrue('root' in rspJson)
        root_uuid = rspJson['root']
        req = self.endpoint + "/groups/" + root_uuid + "/links/test" 
        rsp = requests.get(req)
        self.assertEqual(rsp.status_code, 200)
        rsp = requests.delete(req)  # try to delete the link
        self.assertEqual(rsp.status_code, 403)
        
        
if __name__ == '__main__':
    unittest.main()
