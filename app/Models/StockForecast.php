<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class StockForecast extends Model
{
    protected $fillable = ['stock_id', 'uuid', 'date', 'close'];
    public function stock() {
        return $this->belongsTo(Stock::class);
    }
}
