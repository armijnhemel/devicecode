let
  # Use `niv update` to update nixpkgs.
  # See https://github.com/nmattia/niv/
  sources = import ./nix/sources.nix;

  pkgs = import sources.nixpkgs { config.allowUnfree = true; };

  my-python = pkgs.python3.withPackages (p: with p; [
    click
    cpe
    dataclasses-json
    defusedxml
    mwparserfromhell
    pdfminer
    pillow
    requests
    rich
    textual
  ]);
    
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    git
    my-python
  ];
}
