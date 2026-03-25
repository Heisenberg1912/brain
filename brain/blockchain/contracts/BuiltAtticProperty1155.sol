// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ERC2981} from "@openzeppelin/contracts/token/common/ERC2981.sol";
import {ERC1155Supply} from "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Supply.sol";
import {ERC1155URIStorage} from "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155URIStorage.sol";

/// @title BuiltAtticProperty1155
/// @notice Minimal ERC-1155 contract for tokenized property units.
/// @dev Audit posture:
///      - fixed-supply issuance per property token id
///      - owner-controlled creation only
///      - no upgradeability, no on-chain order book, no escrow logic
///      - rights/compliance remain off-chain in the app layer
contract BuiltAtticProperty1155 is ERC1155Supply, ERC1155URIStorage, ERC2981, Ownable {
    struct PropertyRecord {
        string assetRef;
        bool fractionalEnabled;
    }

    uint256 public nextTokenId = 1;

    mapping(uint256 => PropertyRecord) public propertyRecords;

    event PropertyTokenCreated(
        uint256 indexed tokenId,
        address indexed to,
        uint256 supply,
        string assetRef,
        bool fractionalEnabled
    );

    constructor(address initialOwner) ERC1155("") Ownable(initialOwner) {}

    function createPropertyToken(
        address to,
        uint256 supply,
        string calldata tokenURI_,
        string calldata assetRef,
        bool fractionalEnabled,
        address royaltyReceiver,
        uint96 royaltyBps
    ) external onlyOwner returns (uint256 tokenId) {
        require(to != address(0), "recipient required");
        require(supply > 0, "supply required");
        require(bytes(tokenURI_).length > 0, "token URI required");
        require(fractionalEnabled || supply == 1, "whole property supply must be 1");
        require(royaltyBps <= 10_000, "royalty too high");

        tokenId = nextTokenId;
        nextTokenId += 1;

        _mint(to, tokenId, supply, "");
        _setURI(tokenId, tokenURI_);

        if (royaltyReceiver != address(0) && royaltyBps > 0) {
            _setTokenRoyalty(tokenId, royaltyReceiver, royaltyBps);
        }

        propertyRecords[tokenId] = PropertyRecord({
            assetRef: assetRef,
            fractionalEnabled: fractionalEnabled
        });

        emit PropertyTokenCreated(tokenId, to, supply, assetRef, fractionalEnabled);
    }

    function uri(uint256 tokenId)
        public
        view
        override(ERC1155, ERC1155URIStorage)
        returns (string memory)
    {
        return ERC1155URIStorage.uri(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
