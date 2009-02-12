import webtest

def suite():
    modules = ["test_login", "test_petitions", "test_wyrapi"]
    return webtest.suite(modules)

if __name__ == "__main__":
    webtest.main()
