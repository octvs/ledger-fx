{
  description = "Python application flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake {inherit inputs;} ({...}: {
      systems = import inputs.systems;
      perSystem = {pkgs, ...}: let
        dependencies = with pkgs; [
          # keep-sorted start
          chromedriver
          chromium
          # keep-sorted end
        ];
        pyDependencies = with pkgs.python3.pkgs; [
          # keep-sorted start
          beautifulsoup4
          lxml
          pandas
          selenium
          # keep-sorted end
        ];
        pythonEnv = pkgs.python3.withPackages (ps:
          with ps; [
            selenium
            pandas
            lxml
            beautifulsoup4
          ]);
      in {
        packages.default = pkgs.python3Packages.buildPythonApplication {
          pname = "ledger-fx";
          version = "0-unstable";
          pyproject = true;
          src = ./.;
          build-system = with pkgs.python3.pkgs; [setuptools];
          dependencies = dependencies ++ pyDependencies;
        };
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.chromedriver
            pkgs.chromium
          ];

          shellHook = ''
            echo "Scraper environment ready!"
            echo "Chromium: $(chromium --version)"
            echo "Chromedriver: $(chromedriver --version)"
            echo ""
            echo "Run: python scraper.py"
          '';
        };
      };
    });
}
