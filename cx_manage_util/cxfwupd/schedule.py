""" The Schedule object determines how the firmware updates in a plan
object will be carried out.  It gives guidance to the plan execution engine
on how many updates to do in parallel, when to make updates active, and how to notify someone of problems or eventual completion. """

class schedule:

    def __init__(self):
        self._parallel = -1   # all updates are in parallel
        self._delay = 0
        self._trigger = 'all-done' # activate updates when all are successful
        self._mailto = [] # list of email addresses 

