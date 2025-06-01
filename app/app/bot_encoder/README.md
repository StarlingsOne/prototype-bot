* To generate 10 bots with a ${vibe}

```
./encoder --base ${BASENAME} --vibe "balanced but opportunistic"
```

* Display on terminal after creation for a given base name.

```
for f in ${BASENAME}*.prompt;
  do echo "-----";
  cat "$f"; 
done
```