# Copyright CEA (2011)
# Contributor: TATIBOUET Jeremie <tatibouetj@ocre.cea.fr>

from unittest import TestCase
from MilkCheck.Config.Configuration import MilkCheckConfig
from MilkCheck.ServiceManager import service_manager_self

class MilkCheckConfigTest(TestCase):
    '''Define the test cases of the class MilkCheckConfig'''
    
    def test_instanciation(self):
        '''Try to instanciate an object of the class MilkCheckConfig'''
        self.assertTrue(MilkCheckConfig())
        
    def test_loading_conf_from_stream(self):
        '''Test parsing of a Yaml flow trough a stream'''
        config = MilkCheckConfig()
        config.load_from_stream('''service:
            name: S1
            desc: "I'm the service S1"
            variables:
                LUSTRE_FS_LIST: store0,work0
            target: "@client_lustre"
            actions:
                start:
                    check: status
                    cmd:   shine mount -q -L -f $LUSTRE_FS_LIST
                stop:
                    cmd:   shine umount -q -L -f $LUSTRE_FS_LIST
                status:
                    cmd :  shine status -q -L -f $LUSTRE_FS_LIST
                check:
                    check: status''')
        self.assertTrue(config._flow)
        self.assertTrue(len(config._flow) == 1)

    def test_loading_conf_from_dir(self):
        '''Test parsing of a Yaml existing in a directory'''
        dty = '../tests/MilkCheckTests/ConfigTests/YamlTestFiles/'
        config = MilkCheckConfig()
        config.load_from_dir(directory=dty)
        self.assertTrue(config.data_flow)
        self.assertTrue(len(config.data_flow) == 2)
        config.load_from_dir(directory=dty, recursive=True)
        self.assertTrue(config.data_flow)
        self.assertTrue(len(config.data_flow) > 2)

    def test_load_from_stream(self):
        '''Test parsing of a single YAML stream'''
        config = MilkCheckConfig()
        fi = open('%s%s'
            %('../tests/MilkCheckTests/ConfigTests/',
                'YamlTestFiles/sample_1/sample_1.yaml'), 'r')
        config.load_from_stream(fi)
        fi.close()
        self.assertTrue(config.data_flow)
        self.assertTrue(len(config.data_flow) == 6)
        
    def test_building_graph(self):
        '''Test graph building from configuration'''
        dty = '../tests/MilkCheckTests/ConfigTests/YamlTestFiles/sample_1/'
        config = MilkCheckConfig()
        config.load_from_dir(dty)
        config._build_services()
        # Get back the manager
        manager = service_manager_self()
        self.assertTrue('S1' in manager.entities)
        self.assertTrue('S2' in manager.entities)
        self.assertTrue('S3' in manager.entities)
        self.assertTrue('S4' in manager.entities)
        self.assertTrue(manager.entities['S1'].has_parent_dep('S2'))
        self.assertTrue(manager.entities['S1'].has_parent_dep('S3'))
        self.assertTrue(manager.entities['S3'].has_parent_dep('S4'))
        self.assertTrue(manager.entities['S2'].has_parent_dep('S4'))
        self.assertTrue(manager.entities['S4'].has_parent_dep('G1'))

    def test_parsing_deps(self):
        '''Test parsing of dependencies within a dictionnary'''
        config = MilkCheckConfig()
        wrap = config._parse_deps({'require': ['S1'], 'check': ['S2']})
        self.assertTrue(wrap)
        self.assertTrue('S1' in wrap.deps['require'])
        self.assertTrue('S2' in wrap.deps['check'])
        self.assertFalse(wrap.deps['require_weak'])
        wrap = config._parse_deps({})
        self.assertTrue(wrap)
        self.assertFalse(wrap.deps['require'])
        self.assertFalse(wrap.deps['check'])
        self.assertFalse(wrap.deps['require_weak'])