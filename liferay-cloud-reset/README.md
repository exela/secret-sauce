# Resetting your Cloud Instance - AKA Deleting All DocLib data, ES Indices and lportal/lpartition Database Schemas
The following is a way that you can easily refresh your Liferay instance.  The script should delete your document library data, elastic search indices, and previous databases (lportal or lpartitions).  The script checks for environment variables and will run if they have been set to `true`.


## `LR_HARD_RESET` - Drops all data (Doclib, Indices, and Database)
1. In your environment, add a new environment variable `LR_HARD_RESET` and set it to `true`

2. Place the script, `support-lr-reset.sh`, within the `liferay/configs/common/scripts` folder:

3. Run a `chmod +x support-lr-reset.sh` on the script to ensure it is executable!

4. Submit your PR as usual.

5. Once everything has been reset.  Set the environment variable to `false`.  This should restart your services.

## Other Environment Variables
If you want to save time (or only need) to drop specific things like the Document Library, ES Indices, or Database, instead of using `LIFERAY_HARD_RESET` - you can use the following:

### `DROP_DOCLIB`
Set this to `true` to drop the Document Library.

### `DROP_INDICES`
Set this to `true` to drop Elastic Search Indices.

### `DROP_DATABASE`
Set this to `true` to drop the Liferay databases (and partitions).