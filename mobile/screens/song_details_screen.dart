import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/recognition_history.dart';
import '../providers/playlist_provider.dart';

class SongDetailsScreen extends StatelessWidget {
  final RecognitionHistory song;
  
  const SongDetailsScreen({Key? key, required this.song}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Song Details', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Album cover and song info
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.withOpacity(0.1),
                    blurRadius: 10,
                    offset: Offset(0, 5),
                  ),
                ],
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    // Album cover
                    Container(
                      height: 180,
                      width: 180,
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(8),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.grey.withOpacity(0.3),
                            blurRadius: 15,
                            offset: Offset(0, 5),
                          ),
                        ],
                      ),
                      child: song.albumImage != null && song.albumImage!.isNotEmpty
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: Image.network(
                                song.albumImage!,
                                fit: BoxFit.cover,
                                errorBuilder: (context, error, stackTrace) =>
                                    Icon(Icons.music_note, size: 80, color: Colors.grey[500]),
                              ),
                            )
                          : Icon(Icons.music_note, size: 80, color: Colors.grey[500]),
                    ),
                    SizedBox(height: 16),
                    
                    // Song title
                    Text(
                      song.songTitle,
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    SizedBox(height: 8),
                    
                    // Artist name
                    Text(
                      song.artistName,
                      style: TextStyle(
                        fontSize: 18,
                        color: Colors.grey[600],
                      ),
                    ),
                    SizedBox(height: 4),
                    
                    // Album name if available
                    if (song.albumName != null && song.albumName!.isNotEmpty)
                      Text(
                        'Album: ${song.albumName}',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[500],
                        ),
                      ),
                      
                    SizedBox(height: 16),
                    
                    // Add to playlist button
                    ElevatedButton.icon(
                      onPressed: () => _showAddToPlaylistDialog(context),
                      icon: Icon(Icons.playlist_add),
                      label: Text('Add to Playlist'),
                      style: ElevatedButton.styleFrom(
                        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      ),
                    ),
                    
                    // Favorite button
                    OutlinedButton.icon(
                      onPressed: () {
                        // Favorite functionality to be implemented
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Added to favorites')),
                        );
                      },
                      icon: Icon(Icons.favorite_border),
                      label: Text('Add to Favorites'),
                      style: OutlinedButton.styleFrom(
                        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 16),
            
            // Song details section
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Song Information',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 16),
                  
                  _buildInfoRow('Song ID', song.songId.toString()),
                  _buildInfoRow('Recognized On', _formatDate(song.recognizedAt)),

                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: Colors.grey[900],
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
  
  void _showAddToPlaylistDialog(BuildContext context) {
    final provider = Provider.of<PlaylistProvider>(context, listen: false);
    final userPlaylists = provider.userPlaylists;
    
    if (userPlaylists.isEmpty) {
      _showCreatePlaylistDialog(context);
      return;
    }
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Add to playlist'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              height: 300,
              width: 300,
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: userPlaylists.length,
                itemBuilder: (context, index) {
                  final userPlaylist = userPlaylists[index];
                  return ListTile(
                    leading: Icon(userPlaylist.icon, color: userPlaylist.color),
                    title: Text(userPlaylist.name),
                    onTap: () async {
                      Navigator.pop(context);
                      
                      if (userPlaylist.id != null) {
                        final success = await provider.addSongToPlaylist(userPlaylist.id!, song);
                        
                        if (success) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Added to ${userPlaylist.name}')),
                          );
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Failed to add to playlist')),
                          );
                        }
                      }
                    },
                  );
                },
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _showCreatePlaylistDialog(context);
            },
            child: Text('Create New'),
          ),
        ],
      ),
    );
  }
  
  void _showCreatePlaylistDialog(BuildContext context) {
    final TextEditingController nameController = TextEditingController();
    final TextEditingController descriptionController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Create Playlist'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: InputDecoration(
                hintText: 'Playlist name',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 16),
            TextField(
              controller: descriptionController,
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
              if (nameController.text.trim().isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Please enter a playlist name')),
                );
                return;
              }
              
              Navigator.pop(context);
              
              final provider = Provider.of<PlaylistProvider>(context, listen: false);
              final newPlaylist = await provider.createPlaylist(
                nameController.text.trim(),
                descriptionController.text.trim(),
              );
              
              if (newPlaylist != null && newPlaylist.id != null) {
                final success = await provider.addSongToPlaylist(newPlaylist.id!, song);
                
                if (success) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Added to ${newPlaylist.name}')),
                  );
                }
              }
            },
            child: Text('Create'),
          ),
        ],
      ),
    );
  }
} 