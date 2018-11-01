

test_close_open_close = [
    ['.', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['*', 'State should be Pressed now'],
    ['+', 1],
    ['+', 1],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['*', 'State should be Idle now'],
    ['+', 0],
    ['+', 0],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['*', 'State should be Pressed now'],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 1],
]



test_open_glitch = [
    ['.', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 1],
    ['+', 0],
    ['+', 0],
    ['+', 1],
    ['+', 1],
    ['+', 0],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 0],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['*', 'State should be pressed now'],
    ['+', 1],
    ['+', 1],
    ['+', 1],
]

test_closed_glitch = [
    ['.', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['*', 'State should be pressed now'],
    ['+', 1],
    ['*', 'State should be ACTIVE now'],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 1],
    ['+', 0],
    ['*', 'State should stay ACTIVE'],
    ['+', 1],
    ['+', 0],
    ['+', 0],
    ['*', 'State should stay ACTIVE'],
    ['+', 1],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['*', 'State should stay ACTIVE'],
    ['+', 1],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['+', 0],
    ['*', 'State should be Idle now'],
    ['+', 0],
    ['+', 0],
]

test_cases = {
    'Open-close test' : test_close_open_close,
    'Open-glitch test': test_open_glitch,
    'Closed-glitch test': test_closed_glitch,
}



class TestPB:
    def __init__(self, pb):
        self.pb = pb



    def runTest(self, testCase, name=''):
        tick = 25
        now = 0
        self.pb.reset()

        if len(name):
            print 'Running Test ', name

        print 'Time (msec)\tValue\tState'

        for item in testCase:

            if item[0] == '*':
                print '*** ',item[1]
                continue


            if item[0] == '+':
                now += tick


            ioValue = int(item[1])
            self.pb.setDebug(True,ioValue)
            if now==200:
                pass

            value = self.pb.poll(now)
            print '{0}\t{1}\t{2}'.format(now, ioValue, self.pb.lookup(value))



    def runTestList(self, testList=test_cases):
        for item in testList:
            self.runTest(testList[item], name=item)


