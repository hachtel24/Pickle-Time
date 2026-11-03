import base64,sys
d=sys.argv[1]
t=open(d+'/template.html').read()
t=t.replace('__FONT__',base64.b64encode(open(d+'/dl/mono/dist/Monocraft-ttf/Monocraft.ttf','rb').read()).decode())
t=t.replace('__THREE__',open(d+'/dl/three/package/build/three.min.js').read().replace('</script','<\\/script'))
t=t.replace('__DATA__',open(d+'/data.json').read())
open(sys.argv[2],'w').write(t);print(len(t))
