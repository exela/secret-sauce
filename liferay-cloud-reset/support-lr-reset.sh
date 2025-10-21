#!/bin/bash
set +e

# ==============================================================================
# Deletion Functions
# Each function is responsible for a single task.
# ==============================================================================

# Deletes the document library data folder.
drop_doclib() {
    local doclib_path="/opt/liferay/data/document_library"
    echo "⚙️ Deleting document library content..."

    if [ -d "$doclib_path" ]; then
        # More robustly finds and deletes only the numeric subdirectories
        find "$doclib_path" -mindepth 1 -maxdepth 1 -type d -regex '.*/[0-9]+' -exec rm -rf {} +
        if [ $? -ne 0 ]; then
            echo "❌ ERROR: Failed to delete document library content." >&2
        else
            echo "✅ Document library content deleted."
        fi
    else
        echo "⚠️ Document library not found at $doclib_path, no content deleted."
    fi
}

# Deletes all Elasticsearch indices prefixed with "liferay-".
drop_es_indices() {
    echo "⚙️ Deleting Liferay Elasticsearch indices..."
    local indices_deleted=0
    
    # Reads indices directly into a loop, avoiding temporary files.
    indices_list=$(curl -s -X GET 'search:9200/_cat/indices' | grep 'liferay-' | awk '{ print $3 }')
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Could not connect to Elasticsearch to list indices." >&2
        return 1
    fi

    while read -r index; do
        if [ -n "$index" ]; then # Ensure the line is not empty
            echo "Deleting ES index: ${index}"
            curl -s -X DELETE "search:9200/${index}?pretty" > /dev/null
            if [ $? -ne 0 ]; then
                echo "❌ ERROR: Failed to delete ES index: ${index}" >&2
            else
                indices_deleted=$((indices_deleted + 1))
            fi
        fi
    done <<< "$indices_list"

    if [ "$indices_deleted" -gt 0 ]; then
        echo "✅ Deleted $indices_deleted Liferay Elasticsearch indices."
    else
        echo "⚠️ No Liferay Elasticsearch indices found."
    fi
}

# Drops the lportal database and all lpartition databases for MySQL or PostgreSQL.
drop_database() {
    echo "⚙️ Deleting Liferay database(s)..."
    local dbs_deleted=0

    # --- Check for MySQL ---
    if command -v mysql &> /dev/null; then
        echo "ℹ️ MySQL client found. Proceeding with MySQL cleanup."
        
        db_list=$(mysql -h "database--route" -u "$LCP_SECRET_DATABASE_USER" -p"$LCP_SECRET_DATABASE_PASSWORD" -sN -e "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'lportal' OR schema_name LIKE 'lpartition%';")
        if [ $? -ne 0 ]; then
            echo "❌ ERROR: Could not connect to MySQL to list databases." >&2
            return 1
        fi

        while read -r db_name; do
            if [ -n "$db_name" ]; then
                echo "Dropping MySQL database: ${db_name}"
                mysql -f -h "database--route" -u "$LCP_SECRET_DATABASE_USER" -p"$LCP_SECRET_DATABASE_PASSWORD" -e "DROP DATABASE \`${db_name}\`;"
                if [ $? -ne 0 ]; then
                    echo "❌ ERROR: Failed to drop database: ${db_name}" >&2
                else
                    dbs_deleted=$((dbs_deleted + 1))
                fi
            fi
        done <<< "$db_list"

    # --- Check for PostgreSQL ---
    elif command -v psql &> /dev/null; then
        echo "ℹ️ PostgreSQL client found. Proceeding with PostgreSQL cleanup."
        
        # Temporarily export the password for the psql command to use.
        export PGPASSWORD="$LCP_SECRET_DATABASE_PASSWORD"
        
        db_list=$(psql -h "database--route" -U "$LCP_SECRET_DATABASE_USER" -t -c "SELECT datname FROM pg_database WHERE datname = 'lportal' OR datname LIKE 'lpartition%';")
        if [ $? -ne 0 ]; then
            echo "❌ ERROR: Could not connect to PostgreSQL to list databases." >&2
            unset PGPASSWORD # Unset the password variable
            return 1
        fi

        while read -r db_name; do
            if [ -n "$db_name" ]; then
                echo "Dropping PostgreSQL database: ${db_name}"
                psql -h "database--route" -U "$LCP_SECRET_DATABASE_USER" -c "DROP DATABASE \"${db_name}\";"
                if [ $? -ne 0 ]; then
                    echo "❌ ERROR: Failed to drop database: ${db_name}" >&2
                else
                    dbs_deleted=$((dbs_deleted + 1))
                fi
            fi
        done <<< "$db_list"
        
        # Unset the password variable after use for security
        unset PGPASSWORD
        
    else
        echo "❌ ERROR: No mysql or psql client found. Cannot drop database." >&2
        return 1
    fi

    if [ "$dbs_deleted" -gt 0 ]; then
        echo "✅ Dropped $dbs_deleted Liferay databases."
    else
        echo "⚠️ No Liferay databases or partitions found to delete."
    fi
}

# ==============================================================================
# Main Controller
# This function checks environment variables and calls the appropriate functions.
# ==============================================================================
main() {
    # The master switch: if LR_HARD_RESET is true, enable all individual tasks.
    if [ "${LR_HARD_RESET}" = "true" ]; then
        echo "🚀 LR_HARD_RESET is true. Enabling all deletion tasks."
        export DROP_DOCLIB="true"
        export DROP_INDICES="true"
        export DROP_DATABASE="true"
    fi

    local action_taken=false

    # Trigger individual tasks based on their flags.
    if [ "${DROP_DOCLIB}" = "true" ]; then
        drop_doclib
        action_taken=true
    fi

    if [ "${DROP_INDICES}" = "true" ]; then
        drop_es_indices
        action_taken=true
    fi

    if [ "${DROP_DATABASE}" = "true" ]; then
        drop_database
        action_taken=true
    fi

    # Report the final status and exit if an action was taken.
    if [ "$action_taken" = true ]; then
        echo "🎉 All requested tasks are complete. Please set the DROP variable(s) to false before restarting."
        exit 0
    else
        echo "ℹ️ No action taken. No relevant environment variables were set. Proceeding with application startup."
    fi
}

# Execute the main function
main "${@}"