#!/usr/bin/env python3
import subprocess, sys

def run_sql(sql):
    cmd = ["docker", "exec", "kobaco-db", "psql", "-U", "paperclip", "-d", "paperclip", "-c", sql]
    return subprocess.run(cmd, capture_output=True, text=True)

def list_agents():
    res = run_sql("SELECT name FROM agents WHERE company_id='ebe7e870-9b29-4e42-beb0-37973d78e324' AND adapter_type='hermes_local';")
    if res.returncode != 0:
        print(f"Error listing: {res.stderr}")
        return []
    names = []
    for line in res.stdout.strip().split('\n'):
        if line.strip() and line.strip() not in ('name', '----'):
            names.append(line.strip())
    # Skip headers and footer
    clean = []
    for n in names:
        if '(' not in n and ')' not in n and n not in ['name', '----', 'rows)']:
            clean.append(n)
    print(f"Found {len(clean)} Hermes agents: {clean}")
    return clean

def apply_preset(preset_name, models_str):
    agents = list_agents()
    if not agents:
        print("No hermes_local agents found!")
        return
    
    print(f"\nApplying preset: {preset_name}")
    print(f"Model chain: {models_str}\n")
    
    for name in agents:
        # Get current runtime_config and merge, or create new
        sql = f"UPDATE agents SET runtime_config = '{{\"fallbackModels\": [{models_str}], \"preset\": \"{preset_name}\"}}'::jsonb WHERE name = '{name}';"
        res = run_sql(sql)
        if res.returncode == 0:
            print(f"  OK  - {name}")
        else:
            print(f"  ERR - {name}: {res.stderr.strip()[:100]}")
    
    # Verify
    print("\nVerifying all agents:")
    vres = run_sql("SELECT name, runtime_config->>'preset' as preset, runtime_config->>'fallbackModels' as models FROM agents WHERE runtime_config IS NOT NULL AND runtime_config::text != '{{}}' ORDER BY name;")
    print(vres.stdout)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 /root/koba/scripts/switch-preset.py <preset_name> <model1> <model2> ...")
        sys.exit(1)
    
    preset_name = sys.argv[1]
    models = sys.argv[2:]
    models_str = ", ".join([f'"{m}"' for m in models])
    
    apply_preset(preset_name, models_str)
    print(f"\nAll agents switched to: {preset_name}")

