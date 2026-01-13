#!/bin/zsh

# Define color codes
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

# Define arrays to track installed and failed apps
installed_apps=()
failed_apps=()

# Check if Homebrew is installed and if a specific cask is installed
is_brew_installed() {
  command -v brew &>/dev/null && brew list --cask "$1" &>/dev/null
}

# Function to handle the replacement process for a single app
process_app() {
  app_name="$1"

  echo -e "${BLUE}Attempting to replace: $app_name${RESET}"

  # Attempt to find a matching Homebrew Cask
  brew_cask=$(brew search --cask "$app_name" | head -n 1)

  if [[ -n "$brew_cask" ]]; then
    if is_brew_installed "$brew_cask"; then
      echo -e "${GREEN} -  $app_name is already installed via Homebrew Cask ($brew_cask). Skipping.${RESET}"
    else
      read -q "install_choice? -  Found potential Homebrew Cask: $brew_cask. Install? (y/N) "
      echo
      if [[ "$install_choice" == "y" ]]; then
        echo -e "${YELLOW} -  Installing $brew_cask...${RESET}"
        brew install --cask "$brew_cask" --force
        if [[ $? -eq 0 ]]; then
          echo -e "${GREEN} -  Successfully installed $brew_cask.${RESET}"
          installed_apps+=("$app_name")
        else
          echo -e "${RED} -  Failed to install $brew_cask.${RESET}"
          failed_apps+=("$app_name")
        fi
      else
        failed_apps+=("$app_name")
      fi
    fi
  else
    # Attempt to find a matching Homebrew Formula (for command-line tools)
    brew_formula=$(brew search "$app_name" | head -n 1)
    if [[ -n "$brew_formula" ]]; then
      read -q "install_choice? -  Found potential Homebrew Formula: $brew_formula. Install? (y/N) "
      echo
      if [[ "$install_choice" == "y" ]]; then
        echo -e "${YELLOW} -  Installing $brew_formula...${RESET}"
        brew install "$brew_formula" --force
        if [[ $? -eq 0 ]]; then
          echo -e "${GREEN} -  Successfully installed $brew_formula.${RESET}"
          installed_apps+=("$app_name")
        else
          echo -e "${RED} -  Failed to install $brew_formula.${RESET}"
          failed_apps+=("$app_name")
        fi
      else
        failed_apps+=("$app_name")
      fi
    fi
  fi
  echo ""
}

# Find all installed applications in /Applications
find /Applications -maxdepth 2 -name "*.app" -print0 | while IFS= read -r -d $'\0' app_path; do
  app_name=$(basename "$app_path" .app)
  process_app "$app_name" "$app_path"
done

echo -e "${BLUE}Finished.${RESET}"

# Output list of installed and failed apps
if [[ ${#installed_apps[@]} -gt 0 ]]; then
  echo -e "\n${GREEN}Successfully Installed Apps:${RESET}"
  for app in "${installed_apps[@]}"; do
    echo -e "${GREEN}- $app${RESET}"
  done
else
  echo -e "${YELLOW}No apps were successfully installed.${RESET}"
fi

if [[ ${#failed_apps[@]} -gt 0 ]]; then
  echo -e "\n${RED}Failed Apps:${RESET}"
  for app in "${failed_apps[@]}"; do
    echo -e "${RED}- $app${RESET}"
  done
else
  echo -e "${YELLOW}No apps failed to install.${RESET}"
fi