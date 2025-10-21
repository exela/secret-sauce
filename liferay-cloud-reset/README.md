# Resetting your Cloud Instance - AKA Deleting All DocLib data, ES Indices and lportal/lpartition Database Schemas
The following is a way that you can easily refresh your Liferay instance.  The script should delete your document library data, elastic search indices, and previous databases (lportal or lpartitions).  The script checks for environment variables and will run if they have been set to `true`.


## `LR_HARD_RESET` - Drops all data (Doclib, Indices, and Database)
1. In your Cloud Console environment, add a new environment variable `LR_HARD_RESET` and set it to `true`.

2. Place the script, `support-lr-reset.sh`, within the `liferay/configs/common/scripts` folder.

**NOTE:** There is currently an issue where `common` does not deploy to ALL environments.  To workaround this, use a custom folder for your environment instead: `liferay/configs/achau/scripts`

3. Run a `chmod +x support-lr-reset.sh` on the script to ensure it is executable!

4. Submit your PR and deploy as usual.

5. Wait for the script to run (follow the logs).

6. Once everything has been reset.  Set the environment variable to `false` in Cloud Console.

7. Restart the `database` service.

8. Restart the `liferay` service.

## Other Environment Variables
If you want to save time (or only need) to drop specific things like the Document Library, ES Indices, or Database, instead of using `LR_HARD_RESET` - you can use the following:

### `DROP_DOCLIB`
Set this to `true` to drop the Document Library.

### `DROP_INDICES`
Set this to `true` to drop Elastic Search Indices.

### `DROP_DATABASE`
Set this to `true` to drop the Liferay databases (and partitions).