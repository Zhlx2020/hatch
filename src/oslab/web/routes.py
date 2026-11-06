"""Route table only."""
from . import handlers

ROUTES = [
    ("GET", "/", handlers.index),
    ("GET", "/api/state", handlers.state),
    ("GET", "/api/tree", handlers.tree),
    ("POST", "/api/node", handlers.node_create),
    ("POST", "/api/node/rename", handlers.node_rename),
    ("POST", "/api/node/move", handlers.node_move),
    ("DELETE", "/api/node", handlers.node_delete),
    ("GET", "/api/file/{path:.+}", handlers.file_read),
    ("PUT", "/api/file/{path:.+}", handlers.file_write),
    ("POST", "/api/run", handlers.run),
    ("POST", "/api/step", handlers.step),
    ("POST", "/api/step-over", handlers.step_over),
    ("POST", "/api/cont", handlers.cont),
    ("POST", "/api/pause", handlers.pause),
    ("GET", "/api/serial", handlers.serial),
    ("POST", "/api/reset", handlers.reset),
    ("POST", "/api/bp", handlers.bp_add),
    ("DELETE", "/api/bp/{addr}", handlers.bp_del),
    ("GET", "/api/bps", handlers.bp_list),
    ("POST", "/api/mem", handlers.mem),
    ("POST", "/api/tables", handlers.tables),
    ("GET", "/ws/screen", handlers.screen),
]


def install(app):
    for method, path, handler in ROUTES:
        app.router.add_route(method, path, handler)
