# `target_context` format

In the case `target_table` is a generic grouping table, `target_context` will contain object properties like:

```
{
    "journal_entry": {
        1: {
            "version": 1
        },
        2: {
            "version": 2
        }
    }
}
```

When `target_table` refers to a singular entry, `target_context` will just contain the relevant properties directly like:

```
{
    "version":1
}
```

# `target_context` properties
