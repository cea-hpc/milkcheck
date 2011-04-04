#coding=ISO-8859-1
#contributor: TATIBOUET Jérémie <tatibouetj@ocre.cea.fr>

"""
test
"""

class ServiceStatus(object):
    
    _instance = None
    
    def __new__(self, *args, **kwargs):
        if self._instance is None:
            self._instance =  super(ServiceStatus, self).__new__(
                                self, *args, **kwargs)
        return self._instance
        
	def __init__(self):
		self._enum = [
                        "DOG",
                        "CAT",
                        "Horse"
                     ]

	def __getattr__(self, name):
		if name in self._enum:
			return name

class Factory(object):
    
    _instance = None
    
    def __new__(self, *args, **kwargs):
        if self._instance is None:
            self._instance =  super(Factory, self).__new__(
                                self, *args, **kwargs)
        return self._instance 
    
    def __init__(self):
        self._test = ["15"]
        
    def method1(self):
        print "I'm the method 1"
        

class Car(object):
    
    def __init__(self):
        self._motor = "V8"
        
    def get_motor(self):
        print "setter called"
        return self._motor
    
    def set_motor(self, motor):
        print "getter called"
        if motor != "XX":
            self._motor = motor
            
    motor = property(get_motor,set_motor)
                
if __name__ == "__main__":
    """
    f1 = Factory()
    f2 = Factory()
    print f1
    print f2
    
    st1 = ServiceStatus()
    st2 = ServiceStatus()
    print st1
    print st2
    """
    c = Car()
    print c.motor
    c.motor = "V6"
    print c.motor 