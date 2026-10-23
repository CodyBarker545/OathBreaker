import sys, types, importlib
package = types.ModuleType('assassin_blender_mcp')
package.__path__ = [r'C:\Users\cody_\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\lab_blender_org\mcp']
sys.modules[package.__name__] = package
bridge = importlib.import_module('assassin_blender_mcp.mcp_to_blender_server')
bridge.start('localhost', 9876)
print('ASSASSIN_MCP_READY', flush=True)
while bridge.is_running():
    bridge.poll_blocking()
