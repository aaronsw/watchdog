import webtest

def suite():
    modules = ["test_login", "test_petitions"]
    return webtest.suite(modules)

if __name__ == "__main__":
    webtest.main()
