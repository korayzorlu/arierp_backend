_registry = {}

def register(name):
    def decorator(fn):
        _registry[name] = fn
        return fn
    return decorator

def get_agent_function(name):
    return _registry.get(name)