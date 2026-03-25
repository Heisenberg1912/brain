// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ERC2981} from "@openzeppelin/contracts/token/common/ERC2981.sol";
import {ERC721URIStorage} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

/// @title BuiltAtticPlanRegistry
/// @notice Minimal ERC-721 registry for architectural plans.
/// @dev Audit posture:
///      - no upgradeability
///      - owner-controlled minting only
///      - royalties via ERC-2981
///      - licensing and exchange remain off-chain in the app layer
contract BuiltAtticPlanRegistry is ERC721URIStorage, ERC2981, Ownable {
    struct PlanRecord {
        bytes32 fileHash;
        string versionLabel;
        string licenseCode;
    }

    uint256 public nextTokenId = 1;

    mapping(uint256 => PlanRecord) public planRecords;

    event PlanMinted(
        uint256 indexed tokenId,
        address indexed to,
        bytes32 indexed fileHash,
        string versionLabel,
        string licenseCode
    );
    event PlanTokenURIUpdated(uint256 indexed tokenId, string tokenURI);

    constructor(address initialOwner)
        ERC721("BuiltAttic Plan Registry", "BAPR")
        Ownable(initialOwner)
    {}

    function mintPlan(
        address to,
        string calldata tokenURI_,
        bytes32 fileHash,
        string calldata versionLabel,
        string calldata licenseCode,
        address royaltyReceiver,
        uint96 royaltyBps
    ) external onlyOwner returns (uint256 tokenId) {
        require(to != address(0), "recipient required");
        require(bytes(tokenURI_).length > 0, "token URI required");
        require(royaltyBps <= 10_000, "royalty too high");

        tokenId = nextTokenId;
        nextTokenId += 1;

        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenURI_);

        if (royaltyReceiver != address(0) && royaltyBps > 0) {
            _setTokenRoyalty(tokenId, royaltyReceiver, royaltyBps);
        }

        planRecords[tokenId] = PlanRecord({
            fileHash: fileHash,
            versionLabel: versionLabel,
            licenseCode: licenseCode
        });

        emit PlanMinted(tokenId, to, fileHash, versionLabel, licenseCode);
    }

    function updateTokenURI(uint256 tokenId, string calldata tokenURI_) external onlyOwner {
        require(ownerOf(tokenId) != address(0), "unknown token");
        require(bytes(tokenURI_).length > 0, "token URI required");

        _setTokenURI(tokenId, tokenURI_);
        emit PlanTokenURIUpdated(tokenId, tokenURI_);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721URIStorage, ERC2981)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
