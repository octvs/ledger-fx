{
  description = "Python application flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      runtimeDeps = with pkgs.python3Packages; [selectolax pandas httpx];
      buildDeps = with pkgs.python3Packages; [setuptools];
      selectolax = pkgs.python3Packages.buildPythonPackage rec {
        pname = "selectolax"; # Replace with actual package name
        version = "0.3.25"; # Replace with actual version

        # Fetch from PyPI
        src = pkgs.python3Packages.fetchPypi {
          inherit pname version;
          sha256 = "sha256-Va7jlP6dacgdLG3SRvwhqCKqjQMOPQ3B2S8uj8aLD1o="; # You'll get an error with the correct hash to put here
        };

        # If your package has no tests or you want to skip them
        doCheck = false;
      };
    in {
      packages = rec {
        altinkaynak = pkgs.python3Packages.buildPythonApplication {
          pname = "altinkaynak";
          version = "0.1";
          pyproject = true;
          propagatedBuildInputs = runtimeDeps ++ buildDeps;
          src = ./.;
        };
        default = altinkaynak;
      };

      devShells.default = pkgs.mkShell {buildInputs = runtimeDeps;};
    })
    // {
      overlays.default = final: prev: {altinkaynak = self.packages.${prev.system}.default;};
    };
}
