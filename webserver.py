import subprocess as sub
import json
from flask import Flask, request, jsonify
import requests

PROG = 'timeout 10m python3 main.py'.split()

app = Flask(__name__)

def call_exe(scmd, cwd='.'):
  """ calls external sw with all kind of runtime error suppression """
  assert isinstance(scmd, list) and len(scmd)>0
  print(" run", scmd)
  p = sub.Popen(scmd, stdin=sub.PIPE, stdout=sub.PIPE, stderr=sub.STDOUT, shell=False, cwd=cwd)
  out,err = p.communicate()
  output = ((out or bytes()) + (err or bytes())).decode('ascii', 'ignore').replace('\r', '').strip()
  return p.returncode, output.splitlines()

def is_online(tries=3):
  oUrl = 'https://google.com'
  for retry in range(tries):
    try:
      resp = requests.get(oUrl, timeout=3*(1+retry))
      if resp.status_code == 200:
        return True
    except:
      pass
  return False

@app.route('/get')
def get_coords():
  # comma sep device names
  try:
    names = request.args.get('names').strip()
    assert len(names)>0
    if is_online() is False:
      print('offline')
      assert False
  except:
    return jsonify({'result':'error1'})

  # run
  retval, txt = call_exe(PROG+['-q', names])

  #  eval
  if retval == 0:
    points=[]
    wasError = False

    for line in txt:
      if 'error' in line.lower():
        print(line)

      if line.strip().startswith('JSON '):
        try:
          parsed = json.loads( line.replace('JSON ', '') )
          if 'lat' in parsed: 
            points.append(parsed)
        except:
          print("error parsing line", line)
          wasError = True

    # no points because of error
    if len(points)==0 and wasError:
      return jsonify({'result':'error2', 'points':points})

    # accept point with error
    return jsonify({'result':'ok', 'points':points})

  return jsonify({'result':'error3'})


@app.route('/newkey')
def new_device():
  if is_online() is True:
    # run
    retval, txt = call_exe(PROG+['-a 1'])

    #  eval
    if retval == 0:
      for line in txt:
        if 'error' in line.lower():
          print(line)

        if line.strip().startswith('JSON '):
          try:
            parsed = json.loads( line.replace('JSON ', '') )
            parsed['result'] = 'ok'
            return jsonify(parsed) # first is enough
          except:
            print("error parsing line", line)

  return jsonify({'result':'error'})

# entry point
if __name__ == "__main__":
  PORT=10678  # port <1024 needs root
  print(f"http://127.0.0.1:{PORT}/")
  app.run(host='0.0.0.0', port=PORT, debug = True, use_reloader=False) 
