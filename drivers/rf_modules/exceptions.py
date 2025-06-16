
class BackendRxFault(Exception):
    pass

class NoResponse(Exception):
    def __init__(self, module_id: int):
        msg = 'Module ID: '+str(module_id)
        super().__init__(msg)


class BadResponseModuleID(Exception):
    def __init__(self, module_id: int, actual_id: int):
        msg = 'Module ID must be {0} , got {1} instead'.format(module_id, actual_id)
        super().__init__(msg)


class BadResponseParamID(Exception):
    def __init__(self, module_id: int, param_id: int, actual_param_id: int):
        msg = 'Module ID: {0}. Parameter ID must be {1} , got {2} instead'.format(module_id, param_id, actual_param_id)
        super().__init__(msg)


class RxBufferOverrun(Exception):
    def __init__(self):
        msg = 'Try again'
        super().__init__(msg)