# Design: parsing default user name and default password information

To login to the management interface that many devices have typically a user
name and password are needed. For most devices a default user name and password
have been set by the manufacturer. For some devices a user name and password
are randomly generated.

## Passwords

In TechInfoDepot the default password is stored in the field `defaultpass`.
The default value for this field is:

```
<!-- default Password, Leave blank for unknown -->
```

but there is also this entry, that is used quite a lot (nearly 100 entries):

```
<!-- Leave blank -->
```

It is unclear what this actually means: does it mean that there is a password
but it is simply not known, or does it mean that no password is needed to log
in? There is simply not enough contextual information available to determine
this.

Currently the `<!-- Leave blank -->` entry is ignored, but not as a default
value in `devicecode_defaults.py`. Instead it is ignored in the main code in
`devicecode.py`.

### Blank passwords

Likewise, it isn't clear when a default password is blank, or if it is simply
unknown.

### Password comments

There are also situations where a Wiki user has described the password as there
is no default password and stored it in the `defaultpass` field, as the Wiki
data model doesn't offer another place of storing this information in a
structured way. Some examples found in the TechInfoDepot data are:

```
set at first login
randomly generated
On the back of the router
```

These are clearly not valid passwords. In DeviceCode there is a field
`password_comment` where this value can be stored instead of in the `password`
field.
