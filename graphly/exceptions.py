# -*- coding: utf-8 -*-
class GraphlyError(Exception):
    pass

class NotFoundError(GraphlyError):
    pass

class ExecutionError(GraphlyError):
    pass