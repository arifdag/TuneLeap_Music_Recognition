import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/playlist.dart';
import '../models/recognition_history.dart';
import '../utils/api_config.dart';
import 'auth_service.dart';
import 'history_service.dart';

class PlaylistService {
  final AuthService _authService = AuthService();
  final HistoryService _historyService = HistoryService();
  
  Future<String?> _getAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }
  
  Future<bool> _ensureValidToken() async {
    if (!await _authService.isLoggedIn()) {
      print('User is not logged in');
      return false;
    }
    
    print('User is logged in, validating token...');
    final isValid = await _authService.validateToken();
    print('Token validation result: $isValid');
    return isValid;
  }

  // Get all user playlists
  Future<List<Playlist>> getUserPlaylists() async {
    try {
      if (!await _ensureValidToken()) {
        print('Cannot get playlists: No valid token');
        return [];
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/me/playlists/';
      
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );
      
      if (response.statusCode == 200) {
        try {
          final List<dynamic> data = jsonDecode(response.body);
          
          // Process each playlist to load its songs
          List<Playlist> customPlaylists = [];
          for (var playlistData in data) {
            final playlist = Playlist.fromJson(playlistData);
            // If playlist has ID but no songs, fetch the songs
            if (playlist.id != null && playlist.songs.isEmpty && playlistData['items'] != null) {
              List<RecognitionHistory> songs = [];
              for (var item in playlistData['items']) {
                if (item['song'] != null) {
                  songs.add(RecognitionHistory.fromJson(item['song']));
                }
              }
              // Create a new playlist with the songs
              customPlaylists.add(
                Playlist(
                  id: playlist.id,
                  name: playlist.name,
                  description: playlist.description,
                  type: PlaylistType.custom,
                  icon: playlist.icon,
                  color: playlist.color,
                  songs: songs,
                )
              );
            } else {
              customPlaylists.add(playlist);
            }
          }
          
          return customPlaylists;
        } catch (parseError) {
          print('Error parsing playlists: $parseError');
          return [];
        }
      } else {
        print('Failed to get playlists: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      print('Exception getting playlists: $e');
      return [];
    }
  }

  // Create a new playlist
  Future<Playlist?> createPlaylist(String name, String description) async {
    try {
      if (!await _ensureValidToken()) {
        print('Cannot create playlist: No valid token');
        return null;
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/me/playlists/';
      
      final response = await http.post(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'name': name,
          'description': description
        }),
      );
      
      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return Playlist.fromJson(data);
      } else {
        print('Failed to create playlist: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Exception creating playlist: $e');
      return null;
    }
  }
  
  // Add a song to playlist
  Future<bool> addSongToPlaylist(int playlistId, int songId) async {
    try {
      if (!await _ensureValidToken()) {
        print('Cannot add song to playlist: No valid token');
        return false;
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/me/playlists/$playlistId/songs';
      
      final response = await http.post(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'song_id': songId}),
      );
      
      return response.statusCode == 201;
    } catch (e) {
      print('Exception adding song to playlist: $e');
      return false;
    }
  }
  
  // Get a specific playlist with full song details
  Future<Playlist?> getPlaylistById(int playlistId) async {
    try {
      if (!await _ensureValidToken()) {
        print('Cannot get playlist: No valid token');
        return null;
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/me/playlists/$playlistId';
      
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        List<RecognitionHistory> songs = [];
        
        if (data['items'] != null) {
          for (var item in data['items']) {
            if (item['song'] != null) {
              songs.add(RecognitionHistory.fromJson(item['song']));
            }
          }
        }
        
        return Playlist(
          id: data['id'],
          name: data['name'] ?? 'Unknown Playlist',
          description: data['description'] ?? '',
          type: PlaylistType.custom,
          icon: Icons.queue_music,
          color: Colors.blue,
          songs: songs,
        );
      } else {
        print('Failed to get playlist: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Exception getting playlist: $e');
      return null;
    }
  }
  
  // Remove a song from a playlist
  Future<bool> removeSongFromPlaylist(int playlistId, int songId) async {
    try {
      if (!await _ensureValidToken()) {
        print('Cannot remove song from playlist: No valid token');
        return false;
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/me/playlists/$playlistId/songs/$songId';
      
      final response = await http.delete(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );
      
      return response.statusCode == 204;
    } catch (e) {
      print('Exception removing song from playlist: $e');
      return false;
    }
  }
  
  // Delete a playlist
  Future<bool> deletePlaylist(int playlistId) async {
    try {
      if (!await _ensureValidToken()) {
        print('Cannot delete playlist: No valid token');
        return false;
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/me/playlists/$playlistId';
      
      final response = await http.delete(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );
      
      return response.statusCode == 204;
    } catch (e) {
      print('Exception deleting playlist: $e');
      return false;
    }
  }
  
  // Get auto-generated playlist
  Future<Playlist> getAutoGeneratedPlaylist() async {
    try {
      // Get recently recognized songs as seeds
      final history = await _historyService.getHistoryList(limit: 10);
      if (history.isEmpty) {
        return Playlist.autoGenerated();
      }
      
      // Use the most recent song as seed for auto playlist
      final mostRecentSong = history.first;
      
      if (!await _ensureValidToken()) {
        print('Cannot get auto playlist: No valid token');
        return Playlist.autoGenerated();
      }
      
      final token = await _getAuthToken();
      final url = '${ApiConfig.baseUrl}/playlist/auto?seed_song_id=${mostRecentSong.songId}&top_n=15';
      
      final response = await http.post(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> songIds = jsonDecode(response.body);
        
        // If we have song IDs, try to get the song details
        if (songIds.isNotEmpty) {
          List<RecognitionHistory> songs = [];

          final recentSongs = await _historyService.getHistoryList(limit: songIds.length);
          
          return Playlist(
            name: 'Auto-Generated',
            description: 'Songs similar to your recent recognitions',
            type: PlaylistType.auto,
            icon: Icons.auto_awesome,
            color: Colors.purple,
            songs: recentSongs.take(songIds.length).toList(),
          );
        }
      }
      
      // Return default empty playlist if generation failed
      return Playlist.autoGenerated();
    } catch (e) {
      print('Exception getting auto playlist: $e');
      return Playlist.autoGenerated();
    }
  }
  
  // Generate a new playlist based on user history
  Future<Playlist> generatePlaylistFromHistory() async {
    try {
      // Get full history to use as seeds
      final history = await _historyService.getHistoryList(limit: 30);
      if (history.isEmpty) {
        return Playlist.autoGenerated();
      }
      
      if (!await _ensureValidToken()) {
        print('Cannot generate playlist: No valid token');
        return Playlist.autoGenerated();
      }
      
      // Add a timestamp to make the playlist name unique
      String timestamp = DateTime.now().toString().substring(0, 16);
      

      return Playlist(
        name: 'Generated Playlist ($timestamp)',
        description: 'Based on your listening history',
        type: PlaylistType.auto,
        icon: Icons.auto_awesome,
        color: Colors.purple,
        songs: history.take(15).toList(), // Take up to 15 songs from history
      );
    } catch (e) {
      print('Exception generating playlist: $e');
      return Playlist.autoGenerated();
    }
  }
  
  // Get favorites playlist
  Future<Playlist> getFavoritesPlaylist() async {
    return Playlist.favorites();
  }
  
  // Get recently recognized playlist
  Future<Playlist> getRecentlyRecognizedPlaylist() async {
    try {
      final history = await _historyService.getHistoryList(limit: 20);
      
      // Create the playlist with the fetched songs
      return Playlist(
        name: 'Recently Recognized',
        description: 'Your latest discoveries',
        type: PlaylistType.recent,
        icon: Icons.history,
        color: Colors.blue,
        songs: history,
      );
    } catch (e) {
      print('Exception getting recently recognized: $e');
      return Playlist.recentlyRecognized();
    }
  }
} 