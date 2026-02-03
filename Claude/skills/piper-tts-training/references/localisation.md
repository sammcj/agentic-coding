# Localisation Reference for Non-US English TTS

## espeak-ng Language Codes

| Region | Code | Notes |
|--------|------|-------|
| Australian | en-au | Distinct vowels, non-rhotic |
| British RP | en-gb | Received Pronunciation |
| Scottish | en-gb-scotland | Rhotic, distinct vowels |
| New Zealand | en-nz | Similar to AU with vowel shifts |

Use `en-gb` as fallback if specific variant unavailable.

## Comprehensive Spelling Replacements

Run these substitutions on corpus text before training:

### Suffix patterns
```
-ize → -ise (organise, realise, recognise)
-ization → -isation (organisation, civilisation)
-izing → -ising (organising, recognising)
-ized → -ised (organised, recognised)
-izer → -iser (organiser)

-or → -our (colour, favour, honour, labour, behaviour)
-ored → -oured (coloured, favoured)
-oring → -ouring (colouring, favouring)

-er → -re (centre, metre, theatre, fibre, litre)
-ered → -red (centred)
-ering → -ring (centring)

-og → -ogue (catalogue, dialogue, analogue, prologue)
-ogs → -ogues (catalogues, dialogues)

-ense → -ence (defence, licence, offence, pretence)
-enses → -ences (defences, licences)

-ll- doubled (travelled, cancelled, modelling, labelled)
-l- → -ll- before suffix (travelling, cancelling)
```

### Specific words
```
airplane → aeroplane
aluminum → aluminium
analyze → analyse
canceled → cancelled
catalog → catalogue
center → centre
check (payment) → cheque
color → colour
defense → defence
dialog → dialogue
favor → favour
fiber → fibre
gray → grey
harbor → harbour
honor → honour
humor → humour
jewelry → jewellery
labor → labour
license (noun) → licence
liter → litre
maneuver → manoeuvre
meter → metre
mold → mould
mom → mum
neighbor → neighbour
offense → offence
organize → organise
pajamas → pyjamas
paralyze → paralyse
parlor → parlour
practice (verb US) → practise
program (non-computing) → programme
realize → realise
recognize → recognise
rumor → rumour
savior → saviour
skeptic → sceptic
sulfur → sulphur
theater → theatre
tire → tyre
vapor → vapour
```

## Phonetic Differences

### Vowel shifts to verify
- "dance", "bath", "castle" → /ɑː/ not /æ/
- "schedule" → /ʃ/ not /sk/
- "lieutenant" → /lɛf/ not /luː/
- "herb" → /h/ pronounced
- "been" → /biːn/ not /bɪn/
- "either/neither" → /aɪ/ preferred

### R-colouring
AU/UK/NZ are non-rhotic:
- Final /r/ not pronounced before consonant/pause
- Linking /r/ between vowels across word boundaries
- Intrusive /r/ in some dialects

### -ile endings
- hostile → /aɪl/ not /əl/
- missile → /aɪl/ not /əl/
- fertile → /aɪl/ not /əl/

## Validation Approach

After converting corpus spelling:
1. Run phonemisation with target language code
2. Spot-check distinctive words manually
3. Compare phoneme output for known problem words
4. Re-record or regenerate samples with American pronunciation
