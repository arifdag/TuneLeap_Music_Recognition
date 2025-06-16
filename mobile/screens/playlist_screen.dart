import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/playlist.dart';
import '../providers/playlist_provider.dart';
import 'playlist_details_screen.dart';

class PlaylistScreen extends StatefulWidget {
  @override
  _PlaylistScreenState createState() => _PlaylistScreenState();
}

class _PlaylistScreenState extends State<PlaylistScreen> {
  final TextEditingController _playlistNameController = TextEditingController();
  final TextEditingController _descriptionController = TextEditingController();
  bool _isInit = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_isInit) {
      _loadPlaylists();
      _isInit = true;
    }
  }

  Future<void> _loadPlaylists() async {
    final provider = Provider.of<PlaylistProvider>(context, listen: false);
    await provider.loadAllPlaylists();
  }

  @override
  void dispose() {
    _playlistNameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text('Playlists', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () => _showCreatePlaylistDialog(context),
          ),
        ],
      ),
      body: Consumer<PlaylistProvider>(
        builder: (context, playlistProvider, child) {
          if (playlistProvider.isLoading) {
            return Center(child: CircularProgressIndicator());
          }
          
          final allPlaylists = playlistProvider.allPlaylists;
          
          return RefreshIndicator(
            onRefresh: _loadPlaylists,
            child: allPlaylists.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    padding: EdgeInsets.all(16),
                    itemCount: allPlaylists.length,
                    itemBuilder: (context, index) {
                      final playlist = allPlaylists[index];
                      return _buildPlaylistCard(
                        context,
                        playlist,
                      );
                    },
                  ),
          );
        },
      ),
    );
  }
  
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.queue_music,
            size: 64,
            color: Colors.grey[400],
          ),
          SizedBox(height: 16),
          Text(
            'No playlists yet',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Create your first playlist by tapping the + button',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[500],
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildPlaylistCard(BuildContext context, Playlist playlist) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: playlist.color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(playlist.icon, color: playlist.color, size: 24),
        ),
        title: Text(
          playlist.name,
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        subtitle: Text(playlist.description),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '${playlist.songCount}',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            Text('songs', style: TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PlaylistDetailsScreen(playlist: playlist),
            ),
          ).then((_) {
            // Refresh playlists when returning from details
            _loadPlaylists();
          });
        },
      ),
    );
  }

  void _showCreatePlaylistDialog(BuildContext context) {
    _playlistNameController.clear();
    _descriptionController.clear();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Create Playlist'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _playlistNameController,
              decoration: InputDecoration(
                hintText: 'Playlist name',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 16),
            TextField(
              controller: _descriptionController,
              decoration: InputDecoration(
                hintText: 'Description (optional)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (_playlistNameController.text.trim().isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Please enter a playlist name')),
                );
                return;
              }
              
              Navigator.pop(context);
              
              final provider = Provider.of<PlaylistProvider>(context, listen: false);
              await provider.createPlaylist(
                _playlistNameController.text.trim(),
                _descriptionController.text.trim(),
              );
            },
            child: Text('Create'),
          ),
        ],
      ),
    );
  }
} 